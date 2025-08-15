"""
Text-to-Speech Module for converting text into speech using various providers.

This module provides functionality to convert text into speech using various TTS models.
It supports ElevenLabs, Google, OpenAI and Edge TTS services and handles the conversion process,
including cleaning of input text and merging of audio files.
"""

import io
import logging
import os
import re
import tempfile
from typing import List, Tuple, Optional, Dict, Any

# Import working pydub patch before importing pydub
try:
    from backend.pydub_patch import *
except ImportError:
    try:
        from daytona_ui.pydub_patch import *
    except ImportError:
        # Apply the working patch inline as fallback
        import sys
        import warnings
        import types
        import array
        
        # Create a functional audioop module replacement for Python 3.13+
        try:
            import audioop
        except ImportError:
            class WorkingAudioop:
                """Working audioop implementation for Python 3.13+ compatibility"""
                
                @staticmethod
                def lin2lin(fragment, width, newwidth):
                    """Convert samples between different widths"""
                    if width == newwidth:
                        return fragment
                    
                    # Convert to array for processing
                    if width == 1:
                        fmt = 'b'
                    elif width == 2:
                        fmt = 'h'
                    elif width == 4:
                        fmt = 'l'
                    else:
                        raise ValueError(f"Unsupported width: {width}")
                    
                    if newwidth == 1:
                        newfmt = 'b'
                        maxval = 127
                    elif newwidth == 2:
                        newfmt = 'h'
                        maxval = 32767
                    elif newwidth == 4:
                        newfmt = 'l'
                        maxval = 2147483647
                    else:
                        raise ValueError(f"Unsupported newwidth: {newwidth}")
                    
                    try:
                        # Convert fragment to samples
                        samples = array.array(fmt)
                        samples.frombytes(fragment)
                        
                        # Convert to new width
                        if width < newwidth:
                            # Expanding - multiply by scale factor
                            scale = maxval // (2**(width*8-1) - 1)
                            new_samples = array.array(newfmt, [min(maxval, max(-maxval-1, s * scale)) for s in samples])
                        else:
                            # Shrinking - divide by scale factor  
                            scale = (2**(width*8-1) - 1) // maxval
                            new_samples = array.array(newfmt, [s // scale for s in samples])
                        
                        return new_samples.tobytes()
                    except Exception:
                        # Fallback: return fragment padded or truncated
                        if newwidth > width:
                            # Pad with zeros
                            return fragment + b'\x00' * (len(fragment) * (newwidth - width) // width)
                        else:
                            # Truncate
                            return fragment[::width//newwidth]
                
                @staticmethod 
                def ratecv(fragment, width, nchannels, inrate, outrate, state, weightA=1, weightB=0):
                    """Rate conversion - simplified implementation"""
                    if inrate == outrate:
                        return fragment, state
                    
                    # Simple resampling by duplicating/skipping samples
                    ratio = float(outrate) / inrate
                    frame_size = width * nchannels
                    frames_in = len(fragment) // frame_size
                    frames_out = int(frames_in * ratio)
                    
                    new_fragment = bytearray()
                    for i in range(frames_out):
                        src_frame = int(i / ratio)
                        if src_frame < frames_in:
                            start = src_frame * frame_size
                            end = start + frame_size
                            new_fragment.extend(fragment[start:end])
                    
                    return bytes(new_fragment), state
                
                @staticmethod
                def mul(fragment, width, factor):
                    """Multiply amplitude by factor"""
                    if width == 1:
                        fmt = 'b'
                    elif width == 2:
                        fmt = 'h'  
                    elif width == 4:
                        fmt = 'l'
                    else:
                        return fragment
                    
                    try:
                        samples = array.array(fmt)
                        samples.frombytes(fragment)
                        
                        # Apply factor with clipping
                        if width == 1:
                            maxval = 127
                        elif width == 2:
                            maxval = 32767
                        else:
                            maxval = 2147483647
                        
                        new_samples = array.array(fmt, [
                            min(maxval, max(-maxval-1, int(s * factor))) for s in samples
                        ])
                        return new_samples.tobytes()
                    except Exception:
                        return fragment
                
                def __getattr__(self, name):
                    """Fallback for other audioop methods"""
                    def safe_fallback(*args, **kwargs):
                        # Return reasonable defaults for common operations
                        if name in ['add', 'bias', 'reverse']:
                            return args[0] if args else b''
                        elif name in ['max', 'minmax']:
                            return 0
                        elif name == 'cross':
                            return len(args[0]) if args else 0
                        elif name in ['tomono', 'tostereo']:
                            return args[0] if args else b''
                        else:
                            warnings.warn(f"audioop.{name} fallback used", RuntimeWarning)
                            return args[0] if args else b''
                    return safe_fallback
            
            # Create the module
            audioop = types.ModuleType('audioop')
            working_audioop = WorkingAudioop()
            
            # Add the methods to the module
            audioop.lin2lin = working_audioop.lin2lin
            audioop.ratecv = working_audioop.ratecv
            audioop.mul = working_audioop.mul
            
            # Add other common methods with fallbacks
            for attr in ['add', 'bias', 'cross', 'findfactor', 'findmax', 'getsample', 
                         'max', 'maxpp', 'minmax', 'reverse', 'rms', 'tomono', 'tostereo']:
                setattr(audioop, attr, getattr(working_audioop, attr))
            
            # Add it to sys.modules so pydub can import it
            sys.modules['audioop'] = audioop

        # Also handle pyaudioop
        try:
            import pyaudioop
        except ImportError:
            sys.modules['pyaudioop'] = audioop

from pydub import AudioSegment

from .tts.factory import TTSProviderFactory
from .utils.config import load_config
from .utils.config_conversation import load_conversation_config

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(
        self,
        model: str = None,
        api_key: Optional[str] = None,
        conversation_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the TextToSpeech class.

        Args:
                        model (str): The model to use for text-to-speech conversion.
                                                Options are 'elevenlabs', 'gemini', 'openai', 'edge' or 'geminimulti'. Defaults to 'openai'.
                        api_key (Optional[str]): API key for the selected text-to-speech service.
                        conversation_config (Optional[Dict]): Configuration for conversation settings.
        """
        self.config = load_config()
        self.conversation_config = load_conversation_config(conversation_config)
        self.tts_config = self.conversation_config.get("text_to_speech", {})

        # Get API key from config if not provided
        if not api_key:
            api_key = getattr(self.config, f"{model.upper().replace('MULTI', '')}_API_KEY", None)

        # Initialize provider using factory
        self.provider = TTSProviderFactory.create(
            provider_name=model, api_key=api_key, model=model
        )

        # Setup directories and config
        self._setup_directories()
        self.audio_format = self.tts_config.get("audio_format", "mp3")
        self.ending_message = self.tts_config.get("ending_message", "")

    def _get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        # Get provider name in lowercase without 'TTS' suffix
        provider_name = self.provider.__class__.__name__.lower().replace("tts", "")

        # Get provider config from tts_config
        provider_config = self.tts_config.get(provider_name, {})

        # If provider config is empty, try getting from default config
        if not provider_config:
            provider_config = {
                "model": self.tts_config.get("default_model"),
                "default_voices": {
                    "question": self.tts_config.get("default_voice_question"),
                    "answer": self.tts_config.get("default_voice_answer"),
                },
            }

        logger.debug(f"Using provider config: {provider_config}")
        return provider_config

    def convert_to_speech(self, text: str, output_file: str) -> None:
        """
        Convert input text to speech and save as an audio file.

        Args:
                text (str): Input text to convert to speech.
                output_file (str): Path to save the output audio file.

        Raises:
            ValueError: If the input text is not properly formatted
        """
        # Validate transcript format
        # self._validate_transcript_format(text)

        cleaned_text = text

        try:

            if (
                "multi" in self.provider.model.lower()
            ):  # refactor: We should have instead MultiSpeakerTTS and SingleSpeakerTTS classes
                provider_config = self._get_provider_config()
                voice = provider_config.get("default_voices", {}).get("question")
                voice2 = provider_config.get("default_voices", {}).get("answer")
                model = provider_config.get("model")
                audio_data_list = self.provider.generate_audio(
                    cleaned_text,
                    voice="S",
                    model="en-US-Studio-MultiSpeaker",
                    voice2="R",
                    ending_message=self.ending_message,
                )

                try:
                    # First verify we have data
                    if not audio_data_list:
                        raise ValueError("No audio data chunks provided")

                    logger.info(f"Starting audio processing with {len(audio_data_list)} chunks")
                    combined = AudioSegment.empty()
                    
                    for i, chunk in enumerate(audio_data_list):
                        # Save chunk to temporary file
                        #temp_file = "./tmp.mp3"
                        #with open(temp_file, "wb") as f:
                        #    f.write(chunk)
                        
                        segment = AudioSegment.from_file(io.BytesIO(chunk))
                        logger.info(f"################### Loaded chunk {i}, duration: {len(segment)}ms")
                        
                        combined += segment
                    
                    # Export with high quality settings
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    combined.export(
                        output_file, 
                        format=self.audio_format,
                        codec="libmp3lame",
                        bitrate="320k"
                    )
                    
                except Exception as e:
                    logger.error(f"Error during audio processing: {str(e)}")
                    raise
            else:
                with tempfile.TemporaryDirectory(dir=self.temp_audio_dir) as temp_dir:
                    audio_segments = self._generate_audio_segments(
                        cleaned_text, temp_dir
                    )
                    self._merge_audio_files(audio_segments, output_file)
                    logger.info(f"Audio saved to {output_file}")

        except Exception as e:
            logger.error(f"Error converting text to speech: {str(e)}")
            raise

    def _generate_audio_segments(self, text: str, temp_dir: str) -> List[str]:
        """Generate audio segments for each Q&A pair."""
        qa_pairs = self.provider.split_qa(
            text, self.ending_message, self.provider.get_supported_tags()
        )
        audio_files = []
        provider_config = self._get_provider_config()

        for idx, (question, answer) in enumerate(qa_pairs, 1):
            for speaker_type, content in [("question", question), ("answer", answer)]:
                temp_file = os.path.join(
                    temp_dir, f"{idx}_{speaker_type}.{self.audio_format}"
                )
                voice = provider_config.get("default_voices", {}).get(speaker_type)
                model = provider_config.get("model")

                audio_data = self.provider.generate_audio(content, voice, model)
                with open(temp_file, "wb") as f:
                    f.write(audio_data)
                audio_files.append(temp_file)

        return audio_files

    def _merge_audio_files(self, audio_files: List[str], output_file: str) -> None:
        """
        Merge the provided audio files sequentially, ensuring questions come before answers.

        Args:
                audio_files: List of paths to audio files to merge
                output_file: Path to save the merged audio file
        """
        try:

            def get_sort_key(file_path: str) -> Tuple[int, int]:
                """
                Create sort key from filename that puts questions before answers.
                Example filenames: "1_question.mp3", "1_answer.mp3"
                """
                basename = os.path.basename(file_path)
                # Extract the index number and type (question/answer)
                idx = int(basename.split("_")[0])
                is_answer = basename.split("_")[1].startswith("answer")
                return (
                    idx,
                    1 if is_answer else 0,
                )  # Questions (0) come before answers (1)

            # Sort files by index and type (question/answer)
            audio_files.sort(key=get_sort_key)

            # Create empty audio segment
            combined = AudioSegment.empty()

            # Add each audio file to the combined segment
            for file_path in audio_files:
                combined += AudioSegment.from_file(file_path, format=self.audio_format)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Export the combined audio
            combined.export(output_file, format=self.audio_format)
            logger.info(f"Merged audio saved to {output_file}")

        except Exception as e:
            logger.error(f"Error merging audio files: {str(e)}")
            raise

    def _setup_directories(self) -> None:
        """Setup required directories for audio processing."""
        self.output_directories = self.tts_config.get("output_directories", {})
        temp_dir = self.tts_config.get("temp_audio_dir", "data/audio/tmp/").rstrip("/").split("/")
        self.temp_audio_dir = os.path.join(*temp_dir)
        base_dir = os.path.abspath(os.path.dirname(__file__))
        self.temp_audio_dir = os.path.join(base_dir, self.temp_audio_dir)

        os.makedirs(self.temp_audio_dir, exist_ok=True)

        # Create directories if they don't exist
        for dir_path in [
            self.output_directories.get("transcripts"),
            self.output_directories.get("audio"),
            self.temp_audio_dir,
        ]:
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def _validate_transcript_format(self, text: str) -> None:
        """
        Validate that the input text follows the correct transcript format.

        Args:
            text (str): Input text to validate

        Raises:
            ValueError: If the text is not properly formatted

        The text should:
        1. Have alternating Person1 and Person2 tags
        2. Each opening tag should have a closing tag
        3. Tags should be properly nested
        """
        try:
            # Check for empty text
            if not text.strip():
                raise ValueError("Input text is empty")

            # Check for matching opening and closing tags
            person1_open = text.count("<Person1>")
            person1_close = text.count("</Person1>")
            person2_open = text.count("<Person2>")
            person2_close = text.count("</Person2>")

            if person1_open != person1_close:
                raise ValueError(
                    f"Mismatched Person1 tags: {person1_open} opening tags and {person1_close} closing tags"
                )
            if person2_open != person2_close:
                raise ValueError(
                    f"Mismatched Person2 tags: {person2_open} opening tags and {person2_close} closing tags"
                )

            # Check for alternating pattern using regex
            pattern = r"<Person1>.*?</Person1>\s*<Person2>.*?</Person2>"
            matches = re.findall(pattern, text, re.DOTALL)

            # Calculate expected number of pairs
            expected_pairs = min(person1_open, person2_open)

            if len(matches) != expected_pairs:
                raise ValueError(
                    "Tags are not properly alternating between Person1 and Person2. "
                    "Each Person1 section should be followed by a Person2 section."
                )

                # Check for malformed tags (unclosed or improperly nested)
                stack = []
                for match in re.finditer(r"<(/?)Person([12])>", text):
                    tag = match.group(0)
                    if tag.startswith("</"):
                        if not stack or stack[-1] != tag[2:-1]:
                            raise ValueError(f"Improperly nested tags near: {tag}")
                        stack.pop()
                    else:
                        stack.append(tag[1:-1])

                if stack:
                    raise ValueError(f"Unclosed tags: {', '.join(stack)}")

            logger.debug("Transcript format validation passed")

        except ValueError as e:
            logger.error(f"Transcript format validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transcript validation: {str(e)}")
            raise ValueError(f"Invalid transcript format: {str(e)}")


def main(seed: int = 42) -> None:
    """
    Main function to test the TextToSpeech class.

    Args:
            seed (int): Random seed for reproducibility. Defaults to 42.
    """
    try:
        # Load configuration
        config = load_config()

        # Override default TTS model to use edge for tests
        test_config = {"text_to_speech": {"default_tts_model": "edge"}}

        # Read input text from file
        with open(
            "tests/data/transcript_336aa9f955cd4019bc1287379a5a2820.txt", "r"
        ) as file:
            input_text = file.read()

        # Test ElevenLabs
        tts_elevenlabs = TextToSpeech(model="elevenlabs")
        elevenlabs_output_file = "tests/data/response_elevenlabs.mp3"
        tts_elevenlabs.convert_to_speech(input_text, elevenlabs_output_file)
        logger.info(
            f"ElevenLabs TTS completed. Output saved to {elevenlabs_output_file}"
        )

        # Test OpenAI
        tts_openai = TextToSpeech(model="openai")
        openai_output_file = "tests/data/response_openai.mp3"
        tts_openai.convert_to_speech(input_text, openai_output_file)
        logger.info(f"OpenAI TTS completed. Output saved to {openai_output_file}")

        # Test Edge
        tts_edge = TextToSpeech(model="edge")
        edge_output_file = "tests/data/response_edge.mp3"
        tts_edge.convert_to_speech(input_text, edge_output_file)
        logger.info(f"Edge TTS completed. Output saved to {edge_output_file}")

    except Exception as e:
        logger.error(f"An error occurred during text-to-speech conversion: {str(e)}")
        raise


if __name__ == "__main__":
    main(seed=42)
