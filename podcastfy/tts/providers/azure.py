"""Microsoft Azure Speech Services TTS provider implementation."""

import os
import tempfile
import requests
import json
from typing import List, Optional
from ..base import TTSProvider


class AzureTTS(TTSProvider):
    """Microsoft Azure Speech Services TTS provider."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Azure TTS provider.
        
        Args:
            api_key (str): Azure Speech Services API key
            model (str): Not used for Azure TTS (voice is specified per request)
        """
        self.api_key = api_key or os.getenv('AZURE_SPEECH_KEY')
        self.region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
        
        if not self.api_key:
            raise ValueError("Azure Speech Services API key is required. Set AZURE_SPEECH_KEY environment variable.")
        
        # Azure Speech Services endpoint
        self.endpoint = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"
        
        # Default neural voices
        self.default_voices = {
            'speaker_1': 'en-US-JennyNeural',
            'speaker_2': 'en-US-GuyNeural'
        }
    
    def generate_audio(self, text: str, voice: str, model: str = None, voice2: str = None) -> bytes:
        """
        Generate audio using Azure Speech Services.
        
        Args:
            text (str): Text to convert to speech
            voice (str): Azure voice name (e.g., 'en-US-JennyNeural')
            model (str): Not used for Azure TTS
            voice2 (str): Optional second voice (not used in single generation)
            
        Returns:
            bytes: Generated audio data in MP3 format
        """
        
        # Use default voice if not specified or if generic name provided
        if not voice or voice in ['female', 'male', 'default']:
            voice = self.default_voices['speaker_1']
        
        # Map common voice names to Azure neural voices
        voice_mapping = {
            'rachel': 'en-US-JennyNeural',
            'jenny': 'en-US-JennyNeural', 
            'guy': 'en-US-GuyNeural',
            'davis': 'en-US-DavisNeural',
            'jane': 'en-US-JaneNeural',
            'jason': 'en-US-JasonNeural',
            'sara': 'en-US-SaraNeural',
            'tony': 'en-US-TonyNeural',
            'nancy': 'en-US-NancyNeural',
            'amber': 'en-US-AmberNeural',
            'ana': 'en-US-AnaNeural',
            'ashley': 'en-US-AshleyNeural',
            'brandon': 'en-US-BrandonNeural',
            'christopher': 'en-US-ChristopherNeural',
            'cora': 'en-US-CoraNeural',
            'elizabeth': 'en-US-ElizabethNeural',
            'eric': 'en-US-EricNeural',
            'jacob': 'en-US-JacobNeural',
            'michelle': 'en-US-MichelleNeural',
            'monica': 'en-US-MonicaNeural',
            'roger': 'en-US-RogerNeural',
            'steffan': 'en-US-SteffanNeural'
        }
        
        # Use mapped voice if available
        azure_voice = voice_mapping.get(voice.lower(), voice)
        
        # Prepare SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{azure_voice}">
                <mstts:express-as style="conversational" styledegree="1.0">
                    {self._escape_ssml(text)}
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        # Prepare request headers
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
            'User-Agent': 'PodcastfyAzureTTS'
        }
        
        try:
            # Make request to Azure Speech Services
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=ssml.encode('utf-8'),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                error_msg = f"Azure TTS failed with status {response.status_code}: {response.text}"
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Azure TTS request failed: {str(e)}")
    
    def _escape_ssml(self, text: str) -> str:
        """Escape text for SSML."""
        # Basic SSML escaping
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    def get_supported_tags(self) -> List[str]:
        """Get supported SSML tags for Azure Speech Services."""
        return [
            'speak', 'voice', 'prosody', 'break', 'emphasis', 
            'mstts:express-as', 'mstts:silence', 'phoneme',
            'sub', 'say-as', 'audio'
        ]
    
    def get_available_voices(self) -> dict:
        """
        Get available Azure Neural voices.
        
        Returns:
            dict: Dictionary of available voices by category
        """
        return {
            'neural_voices': {
                'female': [
                    'en-US-JennyNeural',
                    'en-US-JaneNeural', 
                    'en-US-SaraNeural',
                    'en-US-NancyNeural',
                    'en-US-AmberNeural',
                    'en-US-AnaNeural',
                    'en-US-AshleyNeural',
                    'en-US-CoraNeural',
                    'en-US-ElizabethNeural',
                    'en-US-MichelleNeural',
                    'en-US-MonicaNeural'
                ],
                'male': [
                    'en-US-GuyNeural',
                    'en-US-DavisNeural',
                    'en-US-JasonNeural',
                    'en-US-TonyNeural',
                    'en-US-BrandonNeural',
                    'en-US-ChristopherNeural',
                    'en-US-EricNeural',
                    'en-US-JacobNeural',
                    'en-US-RogerNeural',
                    'en-US-SteffanNeural'
                ]
            },
            'premium_voices': {
                'multilingual': [
                    'en-US-AriaNeural',
                    'en-US-JennyMultilingualNeural',
                    'en-US-RyanMultilingualNeural'
                ]
            }
        }
    
    def get_voice_info(self, voice_name: str) -> dict:
        """Get information about a specific voice."""
        voices = self.get_available_voices()
        
        for category, voice_types in voices.items():
            for voice_type, voice_list in voice_types.items():
                if voice_name in voice_list:
                    return {
                        'name': voice_name,
                        'category': category,
                        'type': voice_type,
                        'supported_styles': ['conversational', 'cheerful', 'empathetic', 'newscast', 'excited']
                    }
        
        return {'name': voice_name, 'category': 'unknown', 'type': 'unknown'}