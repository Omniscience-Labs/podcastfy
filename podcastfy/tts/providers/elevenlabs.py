"""ElevenLabs TTS provider implementation."""

from elevenlabs import client as elevenlabs_client
from ..base import TTSProvider
from typing import List

class ElevenLabsTTS(TTSProvider):
    def __init__(self, api_key: str, model: str = "eleven_multilingual_v2"):
        """
        Initialize ElevenLabs TTS provider.
        
        Args:
            api_key (str): ElevenLabs API key
            model (str): Model name to use. Defaults to "eleven_multilingual_v2"
        """
        self.client = elevenlabs_client.ElevenLabs(api_key=api_key)
        self.model = model
        
        # Voice name to ID mapping from your ElevenLabs account
        self.voice_mapping = {
            'chris': 'iP95p4xoKVk53GoZ742B',
            'jessica': 'cgSgspJ2msm6clMCkdW9',
            'george': 'JBFqnCBsd6RMkjVDRZzb',
            'river': 'SAz9YHcvj6GT2YYXdXww',
            'harry': 'SOYHLrjzK2X1ezoPC6cr',
            'charlotte': 'XB0fDUnXU5powFXDhCwa',
            'matilda': 'XrExE9yKIg1WjnnlVkGX',
            'alice': 'Xb7hH8MSUJpSbSDYk0k2',
            'will': 'bIHbv24MWmeRgasZH58o',
            'eric': 'cjVigY5qzO86Huf0OWal',
            'brian': 'nPczCjzI2devNBz1zQrb',
            'lily': 'pFZP5JQG7iQjIQuC4Bku',
            'bill': 'pqHfZKP75CvOlQylNhV4',
            'daniel': 'onwK4e9ZLuTAKqWW03F9',
            'callum': 'N2lVS1w4EtoT3dr4eOWO'
        }
        
    def generate_audio(self, text: str, voice: str, model: str, voice2: str = None) -> bytes:
        """Generate audio using ElevenLabs API."""
        
        # Map voice name to voice ID if needed
        voice_id = self.voice_mapping.get(voice.lower(), voice)
        
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model
        )
        return b''.join(chunk for chunk in audio if chunk)
        
    def get_supported_tags(self) -> List[str]:
        """Get supported SSML tags."""
        return ['lang', 'p', 'phoneme', 's', 'sub'] 