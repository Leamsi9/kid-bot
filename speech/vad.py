import webrtcvad

class VAD:
    def __init__(self):
        self.vad = webrtcvad.Vad(1)

    def is_speech(self, audio_bytes):
        # 30ms, 16kHz, 16bit mono
        return self.vad.is_speech(audio_bytes, 16000)
