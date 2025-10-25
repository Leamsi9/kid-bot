const canvas = document.getElementById('face');
const ctx = canvas.getContext('2d');
const textDiv = document.getElementById('text');
textDiv.style.display = 'none';
const statusDiv = document.getElementById('status');
const installBtn = document.getElementById('installBtn');

let noseLit = false;

let showText = false;

let isSpeaking = false;

let deferredPrompt;
let installTriggered = false;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('Install prompt ready');
});

// Handle install button
installBtn.addEventListener('click', () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install');
            }
            deferredPrompt = null;
            installBtn.style.display = 'none';
        });
    }
});

function initAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        gainNode = audioContext.createGain();
        gainNode.connect(audioContext.destination);
        gainNode.gain.value = 1.0;  // Full volume
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
}
let voiceConfig = {rate: 0.35, pitch: 0.15, volume: 1.0, preferred_voices: ['robot', 'computer', 'synthesizer', 'electronic', 'tts', 'dalek', 'mechanical', 'zira', 'male', 'daniel', 'alex', 'fred', 'tom', 'paul']};
let sttConfig = {provider: 'server'};
let ttsConfig = {provider: 'browser'};
fetch('/config.json').then(response => response.json())
        .then(config => {
            ttsConfig = config.tts || {provider: 'browser'};
            voiceConfig = config.voice || {rate: 1, pitch: 1, volume: 1, preferred_voices: []};
            sttConfig = config.stt || {provider: 'browser'};
            console.log('Config loaded:', {tts: ttsConfig, voice: voiceConfig, stt: sttConfig});
        }).catch(() => {
    console.log('Config not loaded, using defaults');
});

// Make canvas fill the entire screen
function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    drawFace();
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

canvas.addEventListener('click', handleCanvasClick);

function drawFace(jawOpen = 0) {
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    
    // Use the smaller dimension to scale the face
    const scale = Math.min(w, h);
    
    ctx.clearRect(0, 0, w, h);
    
    // Draw antenna
    const antennaY = cy - scale * 0.35;
    const antennaLength = scale * 0.15;
    
    ctx.strokeStyle = showText ? '#ff0' : '#888'; // Light up if text enabled
    ctx.lineWidth = scale * 0.02;
    ctx.beginPath();
    ctx.moveTo(cx - scale * 0.1, antennaY);
    ctx.lineTo(cx - scale * 0.1, antennaY - antennaLength);
    ctx.moveTo(cx + scale * 0.1, antennaY);
    ctx.lineTo(cx + scale * 0.1, antennaY - antennaLength);
    ctx.stroke();
    
    // Antenna balls
    ctx.fillStyle = showText ? '#ff0' : '#888';
    ctx.beginPath();
    ctx.arc(cx - scale * 0.1, antennaY - antennaLength, scale * 0.03, 0, Math.PI * 2);
    ctx.arc(cx + scale * 0.1, antennaY - antennaLength, scale * 0.03, 0, Math.PI * 2);
    ctx.fill();
    
    // Rest of the face...
    
    // Detailed robot head
    const headWidth = scale * 0.85;
    const headHeight = scale * 0.9;
    const headX = cx - headWidth / 2;
    const headY = cy - headHeight / 2;
    
    // Main head (dark metallic)
    const headGradient = ctx.createLinearGradient(headX, headY, headX + headWidth, headY + headHeight);
    headGradient.addColorStop(0, '#3a4556');
    headGradient.addColorStop(0.5, '#4a5568');
    headGradient.addColorStop(1, '#2d3748');
    ctx.fillStyle = headGradient;
    ctx.fillRect(headX, headY, headWidth, headHeight);
    
    // Head border/panel lines
    ctx.strokeStyle = '#1a202c';
    ctx.lineWidth = scale * 0.008;
    ctx.strokeRect(headX, headY, headWidth, headHeight);
    
    // Top panel line
    ctx.beginPath();
    ctx.moveTo(headX, headY + headHeight * 0.15);
    ctx.lineTo(headX + headWidth, headY + headHeight * 0.15);
    ctx.stroke();
    
    // Antenna on top
    ctx.strokeStyle = '#2d3748';
    ctx.lineWidth = scale * 0.012;
    ctx.beginPath();
    ctx.moveTo(cx, headY);
    ctx.lineTo(cx, headY - scale * 0.08);
    ctx.stroke();
    
    // Antenna light (blinking)
    const antennaGlow = ctx.createRadialGradient(cx, headY - scale * 0.08, 0, cx, headY - scale * 0.08, scale * 0.03);
    antennaGlow.addColorStop(0, '#ff4444');
    antennaGlow.addColorStop(0.5, '#cc0000');
    antennaGlow.addColorStop(1, 'rgba(204, 0, 0, 0)');
    ctx.fillStyle = antennaGlow;
    ctx.beginPath();
    ctx.arc(cx, headY - scale * 0.08, scale * 0.03, 0, Math.PI * 2);
    ctx.fill();
    
    // Eyes - large LED displays
    const eyeY = headY + headHeight * 0.35;
    const eyeWidth = scale * 0.18;
    const eyeHeight = scale * 0.15;
    const eyeSpacing = scale * 0.15;
    
    // Left eye background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(cx - eyeSpacing - eyeWidth, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Left eye glow
    const leftEyeGradient = ctx.createRadialGradient(
        cx - eyeSpacing - eyeWidth / 2, eyeY, eyeWidth * 0.1,
        cx - eyeSpacing - eyeWidth / 2, eyeY, eyeWidth * 0.6
    );
    leftEyeGradient.addColorStop(0, '#00ff88');
    leftEyeGradient.addColorStop(0.5, '#00cc66');
    leftEyeGradient.addColorStop(1, '#004422');
    ctx.fillStyle = leftEyeGradient;
    ctx.fillRect(cx - eyeSpacing - eyeWidth, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Left eye border
    ctx.strokeStyle = '#2d3748';
    ctx.lineWidth = scale * 0.006;
    ctx.strokeRect(cx - eyeSpacing - eyeWidth, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Right eye background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(cx + eyeSpacing, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Right eye glow
    const rightEyeGradient = ctx.createRadialGradient(
        cx + eyeSpacing + eyeWidth / 2, eyeY, eyeWidth * 0.1,
        cx + eyeSpacing + eyeWidth / 2, eyeY, eyeWidth * 0.6
    );
    rightEyeGradient.addColorStop(0, '#00ff88');
    rightEyeGradient.addColorStop(0.5, '#00cc66');
    rightEyeGradient.addColorStop(1, '#004422');
    ctx.fillStyle = rightEyeGradient;
    ctx.fillRect(cx + eyeSpacing, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Right eye border
    ctx.strokeRect(cx + eyeSpacing, eyeY - eyeHeight / 2, eyeWidth, eyeHeight);
    
    // Nose/sensor panel
    const noseY = headY + headHeight * 0.55;
    const noseSize = scale * 0.08;
    ctx.fillStyle = '#1a202c';
    ctx.beginPath();
    ctx.arc(cx, noseY, noseSize, 0, Math.PI * 2);
    ctx.fill();
    
    // Small LED on nose
    ctx.fillStyle = noseLit ? '#00ff00' : '#4444ff';
    ctx.beginPath();
    ctx.arc(cx, noseY, noseSize * 0.4, 0, Math.PI * 2);
    ctx.fill();
    
    // Mouth - large speaker grille
    const mouthY = headY + headHeight * 0.72;
    const mouthWidth = scale * 0.5;
    const mouthHeight = scale * 0.18;
    const mouthOpen = jawOpen * scale * 0.06;
    
    // Mouth background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(cx - mouthWidth / 2, mouthY - mouthHeight / 2, mouthWidth, mouthHeight + mouthOpen);
    
    // Speaker grille pattern
    ctx.strokeStyle = '#4a5568';
    ctx.lineWidth = scale * 0.004;
    const grillLines = 20;
    for (let i = 0; i <= grillLines; i++) {
        const x = cx - mouthWidth / 2 + (mouthWidth / grillLines) * i;
        ctx.beginPath();
        ctx.moveTo(x, mouthY - mouthHeight / 2);
        ctx.lineTo(x, mouthY + mouthHeight / 2 + mouthOpen);
        ctx.stroke();
    }
    
    // Horizontal grille lines
    const hLines = 6;
    for (let i = 0; i <= hLines; i++) {
        const y = mouthY - mouthHeight / 2 + ((mouthHeight + mouthOpen) / hLines) * i;
        ctx.beginPath();
        ctx.moveTo(cx - mouthWidth / 2, y);
        ctx.lineTo(cx + mouthWidth / 2, y);
        ctx.stroke();
    }
    
    // Mouth border
    ctx.strokeStyle = '#2d3748';
    ctx.lineWidth = scale * 0.008;
    ctx.strokeRect(cx - mouthWidth / 2, mouthY - mouthHeight / 2, mouthWidth, mouthHeight + mouthOpen);
    
    // Side panels/ears
    const earWidth = scale * 0.08;
    const earHeight = scale * 0.25;
    const earY = cy - earHeight / 2;
    
    // Left ear
    ctx.fillStyle = '#2d3748';
    ctx.fillRect(headX - earWidth * 0.3, earY, earWidth, earHeight);
    ctx.strokeStyle = '#1a202c';
    ctx.lineWidth = scale * 0.004;
    ctx.strokeRect(headX - earWidth * 0.3, earY, earWidth, earHeight);
    
    // Left ear details (bolts)
    for (let i = 0; i < 3; i++) {
        ctx.fillStyle = '#1a202c';
        ctx.beginPath();
        ctx.arc(headX - earWidth * 0.3 + earWidth / 2, earY + earHeight * (0.25 + i * 0.25), scale * 0.015, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // Right ear
    ctx.fillStyle = '#2d3748';
    ctx.fillRect(headX + headWidth - earWidth * 0.7, earY, earWidth, earHeight);
    ctx.strokeRect(headX + headWidth - earWidth * 0.7, earY, earWidth, earHeight);
    
    // Right ear details (bolts)
    for (let i = 0; i < 3; i++) {
        ctx.fillStyle = '#1a202c';
        ctx.beginPath();
        ctx.arc(headX + headWidth - earWidth * 0.2, earY + earHeight * (0.25 + i * 0.25), scale * 0.015, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // Forehead panel with details
    const foreheadY = headY + headHeight * 0.2;
    ctx.strokeStyle = '#5a6578';
    ctx.lineWidth = scale * 0.003;
    ctx.beginPath();
    ctx.moveTo(cx - scale * 0.15, foreheadY);
    ctx.lineTo(cx + scale * 0.15, foreheadY);
    ctx.stroke();
    
    // Small indicator lights on forehead
    const lights = ['#ff4444', '#44ff44', '#4444ff'];
    for (let i = 0; i < 3; i++) {
        ctx.fillStyle = lights[i];
        ctx.beginPath();
        ctx.arc(cx - scale * 0.08 + i * scale * 0.08, foreheadY - scale * 0.02, scale * 0.008, 0, Math.PI * 2);
        ctx.fill();
    }
}

function setStatus(label, color = '#888') {
    statusDiv.textContent = label;
    statusDiv.style.color = 'white';
    statusDiv.style.background = color;
    statusDiv.style.padding = '4px 8px';
    statusDiv.style.borderRadius = '6px';
    statusDiv.style.display = 'inline-block';
    statusDiv.style.marginBottom = '8px';
    
    // Update nose lighting: green when connected and listening, blue otherwise
    noseLit = (label === 'listening…' || label === 'ready' || label === 'thinking…' || label === 'answering…');
    drawFace();
}

let micReady = false;
let ws;

// Initialize Web Speech API
const synth = window.speechSynthesis;
let currentUtterance = null;

let recognition;
if (sttConfig.provider === 'browser') {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.onresult = (event) => {
            if (isSpeaking) return; // Ignore input while speaking
            const transcript = event.results[event.results.length - 1][0].transcript;
            console.log('STT result:', transcript);
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({text: transcript}));
            }
        };
        recognition.onend = () => {
            console.log('STT ended');
            if (micReady && sttConfig.provider === 'browser' && !isSpeaking) {
                recognition.start();
            }
        };
        recognition.onerror = (err) => {
            console.error('STT error:', err);
            setStatus('STT error: ' + err.error, '#d32f2f');
        };
    } else {
        setStatus('STT not supported', '#d32f2f');
    }
}

function toggleConnection() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('Disconnecting...');
        ws.close();
    } else {
        console.log('Connecting...');
        ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
        setupWebSocket();
    }
}

function handleCanvasClick(event) {
    initAudio();  // Initialize audio on user interaction
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const scale = Math.min(w, h);
    const antennaY = cy - scale * 0.35;
    const antennaLength = scale * 0.15;
    const antennaX1 = cx - scale * 0.1;
    const antennaX2 = cx + scale * 0.1;
    const antennaTop = antennaY - antennaLength;
    const antennaRadius = scale * 0.03;
    
    // Trigger install on first click
    if (!installTriggered && deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install');
            }
            deferredPrompt = null;
        });
        installTriggered = true;
    }
    
    // Check if click on antenna
    if ((x >= antennaX1 - antennaRadius && x <= antennaX1 + antennaRadius && y >= antennaY - scale * 0.1 && y <= antennaY) ||
        (x >= antennaX2 - antennaRadius && x <= antennaX2 + antennaRadius && y >= antennaY - scale * 0.1 && y <= antennaY)) {
        toggleConnection();
        return;
    }
    
    // Otherwise, toggle text
    showText = !showText;
    drawFace();
    textDiv.style.display = showText ? 'block' : 'none';
}

function setupWebSocket() {
    ws.onopen = () => {
        console.log('WebSocket opened');
        setStatus('requesting mic...', '#f0ad4e');
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            console.log('Requesting microphone access...');
            navigator.mediaDevices.getUserMedia({audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            }}).then(stream => {
                console.log('Microphone access granted');
                micReady = true;
                setStatus('ready', '#2d6cdf');
                if (sttConfig.provider === 'browser') {
                    if (recognition) {
                        recognition.start();
                    }
                } else {
                    // Server STT: process audio
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)({sampleRate: 16000});
                    const source = audioContext.createMediaStreamSource(stream);
                    const processor = audioContext.createScriptProcessor(512, 1, 1); // ~32ms at 16kHz (closest power of 2)
                    
                    source.connect(processor);
                    processor.connect(audioContext.destination);
                    
                    console.log('Audio processing started');
                    processor.onaudioprocess = (e) => {
                        if (isSpeaking) return; // Skip processing while speaking
                        const inputData = e.inputBuffer.getChannelData(0);
                        // Convert float32 [-1, 1] to int16 PCM
                        const pcm16 = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {
                            const s = Math.max(-1, Math.min(1, inputData[i]));
                            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(pcm16.buffer);
                        }
                    };
                }
            }).catch(err => {
                setStatus('mic blocked: ' + err.name, '#d32f2f');
                console.error('Mic access error:', err);
                console.error('Error name:', err.name);
                console.error('Error message:', err.message);
            });
        } else {
            setStatus('mic not supported', '#d32f2f');
            console.log('getUserMedia not supported');
        }
    };
    // Initialize Web Speech API


    ws.onmessage = e => {
        if (typeof e.data === 'string') {
            try {
                const data = JSON.parse(e.data);
                if (data.state) {
                    switch (data.state) {
                        case 'ready': 
                            if (micReady) setStatus('ready', '#2d6cdf'); 
                            break;
                        case 'listening': setStatus('listening…', '#0a7a0a'); break;
                        case 'processing': setStatus('thinking…', '#f0ad4e'); break;
                        case 'speaking': 
                            setStatus('answering…', '#6f42c1'); 
                            break;
                        case 'idle': setStatus('idle', '#555'); break;
                        case 'error': setStatus('error: '+(data.message||''), '#d32f2f'); break;
                    }
                    return;
                }
                if (data.text) {
                    if (showText) textDiv.textContent = data.text;
                    if (ttsConfig.provider === 'browser') {
                        speakText(data.text);
                    }
                }
            if (data.audio) {
                console.log('Received audio, length:', data.audio.length);
                const audio = new Audio('data:audio/wav;base64,' + data.audio);
                audio.volume = 1.0;
                audio.muted = false;
                let animationInterval;
                audio.onplay = () => {
                    isSpeaking = true;
                    console.log('Audio started playing');
                    // Mouth animation while audio plays
                    animationInterval = setInterval(() => {
                        const jawOpen = Math.random() > 0.5 ? 1 : 0.5;
                        drawFace(jawOpen);
                    }, 150);
                };
                audio.onended = () => {
                    isSpeaking = false;
                    console.log('Audio ended');
                    clearInterval(animationInterval);
                    drawFace(0);
                    setStatus('idle', '#555');
                };
                audio.play().then(() => {
                    console.log('Audio play promise resolved');
                }).catch(err => console.error('Audio play error:', err));
            }
            if (data.log) {
                console.log(data.log);
            }
            if (data.ping) {
                ws.send(JSON.stringify({pong: true}));
            }
        } catch {
            // not JSON, ignore
        }
    }
    // No longer handling binary audio data
};
    ws.onclose = () => setStatus('disconnected', '#999');
    ws.onerror = () => setStatus('error', '#d32f2f');
}

function speakText(text) {
    // Cancel any ongoing speech
    if (currentUtterance) {
        synth.cancel();
        currentUtterance = null;
    }
    
    // Create new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    currentUtterance = utterance;
    
    // Configure voice (try to find a preferred voice)
    const voices = synth.getVoices();
    const preferredVoice = voices.find(v => 
        voiceConfig.preferred_voices.some(p => v.name.toLowerCase().includes(p.toLowerCase()))
    ) || voices.find(v => !v.name.toLowerCase().includes('female') && !v.name.toLowerCase().includes('child')) || voices[0];
    
    if (preferredVoice) {
        utterance.voice = preferredVoice;
        console.log('Using voice:', preferredVoice.name);
        // Send log to server
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({log: 'Using voice: ' + preferredVoice.name}));
        }
    }
    
    // Set speech parameters
    utterance.rate = Math.min(2, voiceConfig.rate);
    utterance.pitch = voiceConfig.pitch;
    utterance.volume = Math.min(1, voiceConfig.volume);
    
    // Animate mouth while speaking
    let animationInterval;
    utterance.onstart = () => {
        isSpeaking = true;
        // Simple mouth animation while speaking
        let jawOpen = 0;
        animationInterval = setInterval(() => {
            jawOpen = Math.random() > 0.5 ? 1 : 0.5;
            drawFace(jawOpen);
        }, 150);
    };
    
    utterance.onend = () => {
        isSpeaking = false;
        clearInterval(animationInterval);
        drawFace(0);
        currentUtterance = null;
        setStatus('idle', '#555');
    };
    
    utterance.onerror = (err) => {
        console.error('Speech error:', err);
        isSpeaking = false;
        clearInterval(animationInterval);
        drawFace(0);
        currentUtterance = null;
    };
    
    // Speak!
    synth.speak(utterance);
}

// Load voices when they become available
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => {
        const voices = speechSynthesis.getVoices();
        console.log('Available voices:', voices.map(v => ({name: v.name, lang: v.lang})));
    };
}

// Start connected
toggleConnection();
