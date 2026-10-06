"""
voice_engine.py
Text-to-speech voice output engine for Orion Web Search Agent.
Uses pyttsx3 in non-blocking threads to read spoken briefs aloud.
"""

import threading
import re
import pyttsx3


class VoiceEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.enabled = False
        self._lock = threading.Lock()

    def set_enabled(self, state: bool):
        self.enabled = state

    def clean_text_for_speech(self, text: str) -> str:
        """Removes markdown symbols, URLs, table lines, and emojis so speech is clean."""
        # Strip code blocks and URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\[\d+\]', '', text)  # [1], [2] citations
        text = re.sub(r'[\*\#\_\|\`\~\━\─\-\=]', ' ', text)
        # Strip emojis
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        # Keep only the first 2-3 sentences for spoken briefing to avoid reading entire tables aloud
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        spoken_part = " ".join(sentences[:3]) if sentences else text[:250]
        return spoken_part.strip()

    def speak(self, text: str):
        """Speaks text synchronously."""
        if not self.enabled:
            return
        cleaned = self.clean_text_for_speech(text)
        if not cleaned:
            return

        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 0.9)
                engine.say(cleaned)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                pass

    def speak_async(self, text: str):
        """Speaks text in a background thread so terminal remains responsive."""
        if not self.enabled:
            return
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()


voice = VoiceEngine()
