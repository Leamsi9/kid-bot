import sys
import argparse
import asyncio
import subprocess
import json
import time
import base64
import gc
import psutil
import os
import torch
import socket
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from speech.vad import VAD
from speech.stt import STT
from brain.llm import LLM
from brain.search import Search
import io

try:
    from transport.bluetooth import start_ble
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

from pyngrok import ngrok
from zeroconf import Zeroconf, ServiceInfo, NonUniqueNameException
import qrcode
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument('--whisper', choices=['tiny', 'large'], default='large')
parser.add_argument('--tunnel', action='store_true')
parser.add_argument('--provider', choices=['ollama', 'api'], default='api', help='Model provider')
parser.add_argument('--model', default='gemini-2.0-flash-exp', help='Model name')
args = parser.parse_args()

# Resource checks and fallbacks
if torch.cuda.is_available():
    free_mem = torch.cuda.mem_get_info()[0]
    if free_mem < 6e9 and args.whisper != 'tiny':
        print("Low free GPU RAM (<6GB). Forcing --whisper tiny to reduce usage.")
        args.whisper = 'tiny'
else:
    print("CUDA not available. Running Whisper on CPU.")
    # CRITICAL: Force tiny model on CPU to prevent system freeze
    if args.whisper != 'tiny':
        print("WARNING: Forcing --whisper tiny on CPU to prevent system overload.")
        args.whisper = 'tiny'

whisper_model = 'tiny.en' if args.whisper == 'tiny' else 'large-v3'

# Load config
import json
config = {}
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except:
    pass

voice_config = config.get('voice', {'rate': 1.0, 'pitch': 0.15, 'volume': 1.0})

# Model selection
model_provider = config.get('model', {}).get('provider', args.provider)
model_name = config.get('model', {}).get('name', args.model)
stt_provider = config.get('stt', {}).get('provider', 'server')
tts_provider = config.get('tts', {}).get('provider', 'browser')

# Set process priority to prevent system freeze
try:
    import os
    os.nice(10)  # Lower priority so system remains responsive
    print("Process priority lowered to prevent system freeze")
except Exception as e:
    print(f"Could not set process priority: {e}")

# Initialize models once at startup
vad_instance = VAD()
stt_instance = STT(whisper_model)
llm_instance = LLM(model_provider, model_name)  # Using selected provider and model
search_instance = Search()

import pyttsx3

def generate_tts(text, voice_config):
    """Generate TTS audio using pyttsx3 with config."""
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_file = f.name
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'male' in voice.name.lower() or 'english' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', int(voice_config.get('rate', 1.0) * 180))
    engine.setProperty('volume', voice_config.get('volume', 1.0))
    # Note: pitch not directly supported in pyttsx3
    engine.save_to_file(text, temp_file)
    engine.runAndWait()
    
    with open(temp_file, 'rb') as f:
        data = f.read()
    
    os.unlink(temp_file)
    return data

print(f"Models initialized. Provider: {model_provider}, Model: {model_name}, Whisper: {whisper_model}, TTS: server")

app = FastAPI()
app.mount("/static", StaticFiles(directory="avatar"), name="static")

@app.get("/")
async def root():
    return FileResponse("avatar/index.html")

@app.get("/config.json")
async def get_config():
    return FileResponse("config.json")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    import numpy as np
    await websocket.accept()
    print("INFO:     connection open")
    vad = vad_instance
    stt = stt_instance
    llm = llm_instance  # Use shared LLM instance
    search = search_instance
    # Per-connection conversation history
    conversation_history = []
    buffer = b''
    silence_time = 0
    sample_rate = 16000
    frame_size = int(0.03 * sample_rate)  # 30ms
    max_buffer_size = sample_rate * 2 * 30  # 30 seconds max (16kHz * 2 bytes * 30s)
    async def send_state(state, message=""):
        try:
            await websocket.send_json({"state": state, "message": message})
        except Exception:
            pass
    last_state = None
    await send_state("ready")
    audio_chunks_received = 0
    speech_frames_detected = 0
    processing_count = 0
    try:
        while True:
            msg = await websocket.receive()
            if msg['type'] == 'websocket.receive':
                if 'text' in msg:
                    try:
                        data = json.loads(msg['text'])
                        if 'log' in data:
                            print(data['log'])
                    except:
                        pass
                elif 'bytes' in msg:
                    # Now receiving raw PCM16 from browser (512 samples = 32ms at 16kHz)
                    pcm = np.frombuffer(msg['bytes'], dtype=np.int16)
                    audio_chunks_received += 1
                    
                    if audio_chunks_received % 100 == 0:
                        print(f"Received {audio_chunks_received} audio chunks, {speech_frames_detected} speech frames, buffer: {len(buffer)} bytes")
                    
                    if len(pcm) < frame_size:
                        continue
                    
                    # VAD requires exact frame sizes: 10ms, 20ms, or 30ms at 16kHz
                    # We have 512 samples (32ms), so process in 480-sample (30ms) chunks
                    for i in range(0, len(pcm) - frame_size + 1, frame_size):
                        frame = pcm[i:i+frame_size]
                        frame_bytes = frame.tobytes()
                        
                        # Prevent buffer overflow - reset if too large
                        if len(buffer) > max_buffer_size:
                            print(f"Buffer overflow detected ({len(buffer)} bytes), resetting...")
                            buffer = b''
                            silence_time = 0
                            continue
                        
                        buffer += frame_bytes
                        
                        is_speech = vad.is_speech(frame_bytes)
                        if is_speech:
                            speech_frames_detected += 1
                        
                        if not is_speech:
                            silence_time += 0.03
                            # Process after 1.0s silence AND minimum 2.0s of audio and some speech detected
                            # Increased thresholds to reduce frequency on empty audio
                            min_buffer_size = sample_rate * 2 * 2.0
                            if silence_time > 1.0 and len(buffer) >= min_buffer_size and speech_frames_detected > 10:
                                processing_count += 1
                                try:
                                    if last_state != "processing":
                                        await send_state("processing")
                                        last_state = "processing"
                                    
                                    # Log system resources every 5th processing
                                    if processing_count % 5 == 0:
                                        mem = psutil.virtual_memory()
                                        print(f"Memory: {mem.percent}% used ({mem.available / 1e9:.1f}GB free)")
                                    
                                    print(f"Transcribing {len(buffer)} bytes ({len(buffer)/(sample_rate*2):.1f}s audio)...")
                                    # Reduced timeout for faster response
                                    start_time = time.time()
                                    try:
                                        text = await asyncio.wait_for(stt.transcribe(buffer), timeout=10.0)
                                        print(f"STT took {time.time() - start_time:.2f}s")
                                    except asyncio.TimeoutError:
                                        print("STT timeout - system overloaded, skipping")
                                        await send_state("idle")
                                        last_state = "idle"
                                        buffer = b''
                                        silence_time = 0
                                        continue
                                    except Exception as e:
                                        print(f"STT error: {e}")
                                        await send_state("idle")
                                        last_state = "idle"
                                        buffer = b''
                                        silence_time = 0
                                        continue
                                    
                                    print(f"Transcribed: {text}")
                                    buffer = b''
                                    silence_time = 0
                                    
                                    # Skip if transcription is empty or too short
                                    if not text or len(text.strip()) < 3:
                                        print("Skipping empty/short transcription")
                                        await send_state("idle")
                                        last_state = "idle"
                                        continue
                                    
                                    if text.strip():  # Only process if we got text
                                        # print(f"Querying context...")
                                        # start_time = time.time()
                                        # try:
                                        #     context = await asyncio.wait_for(search.query(text), timeout=5.0)
                                        #     print(f"Search took {time.time() - start_time:.2f}s")
                                        # except asyncio.TimeoutError:
                                        #     print("Search timeout")
                                        context = ""
                                        
                                        print(f"Generating response...")
                                        start_time = time.time()
                                        try:
                                            response = await asyncio.wait_for(
                                                llm.generate(text, context, conversation_history), 
                                                timeout=30.0
                                            )
                                            print(f"LLM took {time.time() - start_time:.2f}s")
                                        except asyncio.TimeoutError:
                                            print("LLM timeout")
                                            response = "Sorry, I'm taking too long to think. Can you try again?"
                                        
                                        print(f"Response: {response}")
                                        
                                        if last_state != "speaking":
                                            await send_state("speaking")
                                            last_state = "speaking"
                                        
                                        # Send text response
                                        print(f"Sending response...")
                                        if tts_provider == 'server':
                                            # Generate TTS audio
                                            audio_data = await asyncio.to_thread(generate_tts, response, voice_config)
                                            print(f"Audio generated: {len(audio_data)} bytes")
                                            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                                            await websocket.send_json({'text': response, 'audio': audio_b64})
                                        else:
                                            await websocket.send_json({'text': response})
                                    
                                    await send_state("idle")
                                    last_state = "idle"
                                    
                                    # Aggressive cleanup to prevent memory accumulation
                                    gc.collect()
                                    if torch.cuda.is_available():
                                        torch.cuda.empty_cache()
                                    
                                    # Log memory after processing every 5th
                                    if processing_count % 5 == 0:
                                        mem = psutil.virtual_memory()
                                        print(f"Memory after processing: {mem.percent}% used ({mem.available / 1e9:.1f}GB free)")
                                except Exception as e:
                                    print(f"Error in processing: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    await send_state("error", str(e))
                                    buffer = b''
                                    silence_time = 0
                        else:
                            silence_time = 0
                            if last_state != "listening":
                                await send_state("listening")
                                last_state = "listening"
    except Exception as e:
        print(f"INFO:     connection closed: {e}")
    finally:
        # Cleanup resources
        buffer = b''
        conversation_history.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("INFO:     connection closed")

def decode_audio(blob, sample_rate):
    try:
        # Decode Opus to PCM16k mono
        container = av.open(io.BytesIO(blob))
        stream = container.streams.audio[0]
        pcm = []
        for frame in container.decode(stream):
            pcm.extend(frame.to_ndarray().flatten())
        return np.array(pcm, dtype=np.int16)
    except Exception as e:
        print(f"Audio decode error: {e}")
        return np.array([], dtype=np.int16)

if args.tunnel:
    url = ngrok.connect(8000).public_url
    print(f"Tunnel: {url}")
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii()
elif BLE_AVAILABLE and not args.tunnel:
    asyncio.create_task(start_ble())
    print("Pair 'ChipBot' in iPad Settings")
else:
    zeroconf = Zeroconf()
    base_name = "ChipBot"
    service_type = "_http._tcp.local."
    name = f"{base_name}._http._tcp.local."
    info = ServiceInfo(service_type, name, addresses=[socket.inet_aton('0.0.0.0')], port=8000)
    try:
        zeroconf.register_service(info)
    except NonUniqueNameException:
        # Try with a numeric suffix until we find a unique name
        for i in range(2, 11):
            alt_name = f"{base_name}-{i}._http._tcp.local."
            info = ServiceInfo(service_type, alt_name, addresses=[socket.inet_aton('0.0.0.0')], port=8000)
            try:
                zeroconf.register_service(info)
                break
            except NonUniqueNameException:
                continue
    ip = socket.gethostbyname(socket.gethostname())
    print(f"WiFi: http://{ip}:8000")

uvicorn.run(app, host="0.0.0.0", port=8000)
