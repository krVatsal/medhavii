#!pip install elevenlabs requests pydub langdetect azure-cognitiveservices-speech -q
#!apt-get install -y ffmpeg -q

import os
import re
import json
import requests
import time
from typing import List, Dict, Optional, Tuple
from io import BytesIO
import math

try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Installing langdetect...")
    os.system("pip install langdetect")
    from langdetect import detect, LangDetectException

try:
    from pydub import AudioSegment
except ImportError:
    print("Installing pydub...")
    os.system("pip install pydub")
    from pydub import AudioSegment

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("Installing Azure Speech SDK...")
    os.system("pip install azure-cognitiveservices-speech")
    import azure.cognitiveservices.speech as speechsdk

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load API keys from environment
def _load_elevenlabs_accounts():
    """Load ElevenLabs accounts from environment variables."""
    accounts = []
    for i in range(1, 5):  # Support up to 4 accounts
        key = os.getenv(f"ELEVENLABS_API_KEY_{i}")
        if key:
            accounts.append({
                "api_key": key,
                "name": f"Account {i}",
                "total_seconds": 600,  # 10 minutes per account
                "used_seconds": 0,
            })
    return accounts

ELEVENLABS_ACCOUNTS = _load_elevenlabs_accounts()

# Azure Configuration from environment
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_REGION = os.getenv("AZURE_REGION", "eastus")

# Azure Voice Configuration for Indian Languages
AZURE_VOICES = {
    "en": "en-IN-NeerjaNeural",  # English (India)
    "hi": "hi-IN-SwaraNeural",   # Hindi
    "ta": "ta-IN-PallaviNeural", # Tamil
    "te": "te-IN-ShrutiNeural",  # Telugu
    "mr": "mr-IN-AarohiNeural",  # Marathi
    "bn": "bn-IN-TanishaaNeural",# Bengali
    "gu": "gu-IN-DhwaniNeural",  # Gujarati
    "kn": "kn-IN-SapnaNeural",   # Kannada
    "ml": "ml-IN-SobhanaNeural", # Malayalam
    "pa": "pa-IN-AnjaliNeural",  # Punjabi
    "ur": "ur-IN-GulNeural",     # Urdu
}

# ElevenLabs Settings
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Words per minute for duration estimation (language-specific)
WORDS_PER_MINUTE = {
    "en": 150,  # English
    "hi": 140,  # Hindi
    "ta": 130,  # Tamil
    "te": 135,  # Telugu
    "mr": 140,  # Marathi
    "bn": 140,  # Bengali
    "gu": 140,  # Gujarati
    "kn": 135,  # Kannada
    "ml": 135,  # Malayalam
    "pa": 140,  # Punjabi
    "ur": 140,  # Urdu
    "default": 140
}

# Safety buffer (percentage) for duration estimates
DURATION_SAFETY_BUFFER = 1.15  # 15% buffer

# Maximum chunk duration (90% of 10 minutes for safety)
MAX_CHUNK_DURATION_SECONDS = 540  # 9 minutes

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_audio_duration(text: str, language: str = "en") -> float:
    """
    Estimate audio duration in seconds based on word count and language.

    Args:
        text: Input text
        language: ISO language code (en, hi, ta, etc.)

    Returns:
        Estimated duration in seconds with safety buffer
    """
    word_count = len(text.split())
    wpm = WORDS_PER_MINUTE.get(language, WORDS_PER_MINUTE["default"])

    # Calculate base duration
    duration_minutes = word_count / wpm
    duration_seconds = duration_minutes * 60

    # Apply safety buffer
    return duration_seconds * DURATION_SAFETY_BUFFER


def split_text_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences intelligently, handling multiple languages.

    Supports:
    - English: . ! ?
    - Hindi/Sanskrit: । ॥
    - Tamil: । ஃ
    """
    # Sentence ending patterns for multiple languages
    sentence_pattern = r'([.!?।॥]+\s*)'

    parts = re.split(sentence_pattern, text)

    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
        sentence = sentence.strip()
        if sentence:
            sentences.append(sentence)

    # If no sentences found, return the whole text
    return sentences if sentences else [text]


def chunk_text_by_duration(
    text: str,
    max_duration_seconds: float,
    language: str = "en"
) -> List[str]:
    """
    Split text into chunks that don't exceed max_duration_seconds.

    Args:
        text: Input text to split
        max_duration_seconds: Maximum duration per chunk
        language: Language code for WPM calculation

    Returns:
        List of text chunks
    """
    sentences = split_text_into_sentences(text)
    chunks = []
    current_chunk = []
    current_duration = 0.0

    for sentence in sentences:
        sentence_duration = estimate_audio_duration(sentence, language)

        # If adding this sentence keeps us under limit, add it
        if current_duration + sentence_duration <= max_duration_seconds:
            current_chunk.append(sentence)
            current_duration += sentence_duration
        else:
            # Save current chunk if it exists
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            # Check if single sentence exceeds max duration
            if sentence_duration > max_duration_seconds:
                # Split sentence by words
                words = sentence.split()
                word_chunk = []
                word_duration = 0.0

                for word in words:
                    word_dur = estimate_audio_duration(word, language)

                    if word_duration + word_dur <= max_duration_seconds:
                        word_chunk.append(word)
                        word_duration += word_dur
                    else:
                        if word_chunk:
                            chunks.append(" ".join(word_chunk))
                        word_chunk = [word]
                        word_duration = word_dur

                if word_chunk:
                    chunks.append(" ".join(word_chunk))

                current_chunk = []
                current_duration = 0.0
            else:
                # Start new chunk with current sentence
                current_chunk = [sentence]
                current_duration = sentence_duration

    # Add remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def merge_audio_chunks(audio_bytes_list: List[bytes]) -> bytes:
    """
    Merge multiple audio byte arrays into a single audio file.

    Args:
        audio_bytes_list: List of audio data as bytes

    Returns:
        Merged audio as bytes
    """
    if not audio_bytes_list:
        return None

    if len(audio_bytes_list) == 1:
        return audio_bytes_list[0]

    # Load first audio segment
    combined = AudioSegment.from_file(BytesIO(audio_bytes_list[0]))

    # Sequentially append remaining segments
    for audio_bytes in audio_bytes_list[1:]:
        segment = AudioSegment.from_file(BytesIO(audio_bytes))
        combined += segment

    # Export to bytes
    output_buffer = BytesIO()
    combined.export(output_buffer, format="mp3")
    return output_buffer.getvalue()


def detect_language(text: str) -> str:
    """
    Detect language of the input text.

    Returns:
        ISO language code (e.g., 'en', 'hi', 'ta')
    """
    try:
        return detect(text)
    except LangDetectException:
        return "en"  # Default to English


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


# ============================================================================
# ELEVENLABS MANAGER
# ============================================================================

class ElevenLabsAccountManager:
    """
    Manages multiple ElevenLabs accounts with intelligent credit tracking
    and automatic account rotation.
    """

    def __init__(self, accounts: List[Dict]):
        self.accounts = accounts
        self.current_index = 0
        self.base_url = "https://api.elevenlabs.io/v1"

    def get_remaining_seconds(self, account: Dict) -> float:
        """Get remaining seconds for an account."""
        return account["total_seconds"] - account["used_seconds"]

    def find_available_account(self, required_duration: float) -> Optional[int]:
        """
        Find an account with sufficient credits for the required duration.

        Args:
            required_duration: Duration needed in seconds

        Returns:
            Index of available account or None
        """
        # Try current account first
        if self.get_remaining_seconds(self.accounts[self.current_index]) >= required_duration:
            return self.current_index

        # Search all accounts
        for i, account in enumerate(self.accounts):
            if self.get_remaining_seconds(account) >= required_duration:
                return i

        return None

    def use_credits(self, account_index: int, duration: float):
        """Record credit usage for an account."""
        self.accounts[account_index]["used_seconds"] += duration

    def synthesize_text(
        self,
        text: str,
        voice_id: str = ELEVENLABS_VOICE_ID,
        model: str = ELEVENLABS_MODEL
    ) -> Optional[bytes]:
        """
        Synthesize text to speech, handling account rotation automatically.

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            model: ElevenLabs model ID

        Returns:
            Audio data as bytes or None if failed
        """
        language = detect_language(text)
        estimated_duration = estimate_audio_duration(text, language)

        print(f"\nEstimated duration: {format_duration(estimated_duration)}")

        # Find available account
        account_index = self.find_available_account(estimated_duration)

        if account_index is None:
            print("❌ No ElevenLabs account has sufficient credits")
            return None

        # Switch to available account if needed
        if account_index != self.current_index:
            self.current_index = account_index
            print(f"→ Switched to {self.accounts[account_index]['name']}")

        account = self.accounts[account_index]

        # Make API request
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": account["api_key"]
        }

        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code == 200:
                # Record credit usage
                self.use_credits(account_index, estimated_duration)

                remaining = self.get_remaining_seconds(account)
                print(f"✅ Synthesis successful | {account['name']} | "
                      f"Used: {format_duration(estimated_duration)} | "
                      f"Remaining: {format_duration(remaining)}")

                return response.content

            elif response.status_code == 401:
                print(f"❌ Authentication failed for {account['name']}")
                return None

            elif response.status_code == 429:
                print(f"❌ Rate limit exceeded for {account['name']}")
                return None

            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("❌ Request timeout")
            return None

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None

    def synthesize_long_text(
        self,
        text: str,
        voice_id: str = ELEVENLABS_VOICE_ID,
        model: str = ELEVENLABS_MODEL
    ) -> Optional[bytes]:
        """
        Synthesize long text by intelligently chunking and merging.

        Args:
            text: Long text to synthesize
            voice_id: ElevenLabs voice ID
            model: ElevenLabs model ID

        Returns:
            Merged audio data as bytes or None if failed
        """
        language = detect_language(text)
        total_duration = estimate_audio_duration(text, language)

        print("\n" + "="*70)
        print("ELEVENLABS LONG TEXT SYNTHESIS")
        print("="*70)
        print(f"Text length: {len(text)} chars, {len(text.split())} words")
        print(f"Language: {language}")
        print(f"Total estimated duration: {format_duration(total_duration)}")
        print("="*70)

        # Check if we have enough total credits
        total_available = sum(self.get_remaining_seconds(acc) for acc in self.accounts)

        if total_available < total_duration:
            print(f"\n❌ Insufficient total credits!")
            print(f"   Required: {format_duration(total_duration)}")
            print(f"   Available: {format_duration(total_available)}")
            return None

        # Split text into chunks
        chunks = chunk_text_by_duration(text, MAX_CHUNK_DURATION_SECONDS, language)

        print(f"\nSplit into {len(chunks)} chunks")
        print("-"*70)

        audio_segments = []

        for i, chunk in enumerate(chunks):
            chunk_duration = estimate_audio_duration(chunk, language)

            print(f"\nChunk {i+1}/{len(chunks)}")
            print(f"Duration: {format_duration(chunk_duration)}")
            print(f"Text preview: {chunk[:80]}...")

            # Synthesize chunk
            audio_data = self.synthesize_text(chunk, voice_id, model)

            if audio_data:
                audio_segments.append(audio_data)
            else:
                print(f"❌ Chunk {i+1} failed")
                return None

            # Small delay between requests
            if i < len(chunks) - 1:
                time.sleep(0.5)

        # Merge all audio segments
        if len(audio_segments) == len(chunks):
            print("\n" + "-"*70)
            print(f"Merging {len(audio_segments)} audio segments...")
            merged_audio = merge_audio_chunks(audio_segments)
            print("✅ Audio merging complete")
            print("="*70)
            return merged_audio

        return None

    def get_status(self) -> str:
        """Get status report of all accounts."""
        lines = ["\n" + "="*70]
        lines.append("ELEVENLABS ACCOUNT STATUS")
        lines.append("="*70)

        for i, account in enumerate(self.accounts):
            used = account["used_seconds"]
            total = account["total_seconds"]
            remaining = total - used
            used_pct = (used / total) * 100

            status_marker = "→" if i == self.current_index else " "

            lines.append(
                f"{status_marker} {account['name']}: "
                f"{format_duration(remaining)} remaining "
                f"({used_pct:.1f}% used)"
            )

        total_remaining = sum(self.get_remaining_seconds(acc) for acc in self.accounts)
        lines.append("-"*70)
        lines.append(f"Total remaining: {format_duration(total_remaining)}")
        lines.append("="*70)

        return "\n".join(lines)


# ============================================================================
# AZURE TTS
# ============================================================================

class AzureTTS:
    """Azure Text-to-Speech provider with support for all Indian languages."""

    def __init__(self, speech_key: str, region: str):
        self.speech_key = speech_key
        self.region = region

        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.region
        )

    def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_name: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate speech using Azure TTS.

        Args:
            text: Text to synthesize
            language: Language code (en, hi, ta, etc.)
            voice_name: Specific voice name (optional, will use default for language)

        Returns:
            Audio data as bytes or None if failed
        """
        # Select voice based on language
        if not voice_name:
            voice_name = AZURE_VOICES.get(language, AZURE_VOICES["en"])

        self.speech_config.speech_synthesis_voice_name = voice_name

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None  # Set audio_config to None to get audio data directly from result
        )

        try:
            # Synthesize
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"✅ Azure TTS synthesis successful (Voice: {voice_name})")
                return result.audio_data

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"❌ Azure TTS canceled: {cancellation.reason}")

                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"   Error details: {cancellation.error_details}")

                return None

            else:
                print(f"❌ Azure TTS failed with reason: {result.reason}")
                return None

        except Exception as e:
            print(f"❌ Azure TTS Exception: {str(e)}")
            return None

    def synthesize_long_text(
        self,
        text: str,
        language: str = "en",
        voice_name: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Synthesize long text by chunking and merging.

        Args:
            text: Long text to synthesize
            language: Language code
            voice_name: Specific voice name (optional)

        Returns:
            Merged audio data as bytes or None if failed
        """
        total_duration = estimate_audio_duration(text, language)

        print("\n" + "="*70)
        print("AZURE TTS LONG TEXT SYNTHESIS")
        print("="*70)
        print(f"Text length: {len(text)} chars, {len(text.split())} words")
        print(f"Language: {language}")
        print(f"Total estimated duration: {format_duration(total_duration)}")

        # Select voice
        if not voice_name:
            voice_name = AZURE_VOICES.get(language, AZURE_VOICES["en"])
        print(f"Voice: {voice_name}")
        print("="*70)

        # For Azure, we can handle longer texts, but still chunk for safety
        # Azure supports up to 10 minutes per request
        chunks = chunk_text_by_duration(text, MAX_CHUNK_DURATION_SECONDS, language)

        if len(chunks) > 1:
            print(f"\nSplit into {len(chunks)} chunks")
            print("-"*70)

        audio_segments = []

        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                chunk_duration = estimate_audio_duration(chunk, language)
                print(f"\nChunk {i+1}/{len(chunks)}")
                print(f"Duration: {format_duration(chunk_duration)}")
                print(f"Text preview: {chunk[:80]}...")

            # Synthesize chunk
            audio_data = self.synthesize(chunk, language, voice_name)

            if audio_data:
                audio_segments.append(audio_data)
            else:
                print(f"❌ Chunk {i+1} failed")
                return None

            # Small delay between requests
            if i < len(chunks) - 1:
                time.sleep(0.3)

        # Merge if multiple chunks
        if len(audio_segments) > 1:
            print("\n" + "-"*70)
            print(f"Merging {len(audio_segments)} audio segments...")
            merged_audio = merge_audio_chunks(audio_segments)
            print("✅ Audio merging complete")
            print("="*70)
            return merged_audio
        elif len(audio_segments) == 1:
            print("="*70)
            return audio_segments[0]

        return None


# ============================================================================
# MAIN TTS SYSTEM
# ============================================================================

class MultiProviderTTS:
    """
    Main TTS system with intelligent routing and management.
    """

    def __init__(
        self,
        elevenlabs_accounts: List[Dict],
        azure_speech_key: str,
        azure_region: str,
        output_dir: str = "tts_output"
    ):
        self.elevenlabs = ElevenLabsAccountManager(elevenlabs_accounts)
        self.azure = AzureTTS(azure_speech_key, azure_region)
        self.output_dir = output_dir

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n✅ TTS System initialized")
        print(f"   Output directory: {output_dir}")
        print(f"   ElevenLabs accounts: {len(elevenlabs_accounts)}")
        print(f"   Azure region: {azure_region}")

    def generate_speech(
        self,
        text: str,
        output_filename: str = "output.mp3",
        language: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate speech with automatic provider selection.

        Args:
            text: Input text to synthesize
            output_filename: Name of output file
            language: Force specific language (optional)
            provider: Force specific provider ('elevenlabs' or 'azure')

        Returns:
            Path to saved audio file or None if failed
        """
        print("\n" + "#"*70)
        print("GENERATING SPEECH")
        print("#"*70)
        print(f"Text: {text[:100]}...")
        print(f"Length: {len(text)} chars, {len(text.split())} words")

        # Detect language if not provided
        if not language:
            language = detect_language(text)

        print(f"Language: {language}")

        audio_data = None

        # Provider selection logic
        if provider:
            print(f"Forced provider: {provider}")

            if provider == "elevenlabs":
                audio_data = self.elevenlabs.synthesize_long_text(text)
            elif provider == "azure":
                audio_data = self.azure.synthesize_long_text(text, language)

        else:
            # Automatic routing based on language
            # Azure for Indian languages and English
            # ElevenLabs as fallback

            if language in AZURE_VOICES:
                # Language supported by Azure
                print(f"Provider: Azure TTS (with ElevenLabs fallback)")
                audio_data = self.azure.synthesize_long_text(text, language)

                if not audio_data:
                    print("\nAzure failed, falling back to ElevenLabs...")
                    audio_data = self.elevenlabs.synthesize_long_text(text)

            else:
                # Use ElevenLabs for other languages
                print(f"Provider: ElevenLabs (primary for {language})")
                audio_data = self.elevenlabs.synthesize_long_text(text)

        # Save audio file
        if audio_data:
            output_path = os.path.join(self.output_dir, output_filename)

            with open(output_path, "wb") as f:
                f.write(audio_data)

            file_size = len(audio_data) / 1024  # KB

            print("\n" + "#"*70)
            print(f"✅ SUCCESS")
            print(f"   File: {output_path}")
            print(f"   Size: {file_size:.1f} KB")
            print("#"*70 + "\n")

            return output_path

        else:
            print("\n" + "#"*70)
            print("❌ FAILED - Could not generate audio")
            print("#"*70 + "\n")
            return None

    def batch_generate(
        self,
        items: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Process multiple texts in batch.

        Args:
            items: List of dicts with 'text', 'filename', and optional 'language'

        Returns:
            List of results with status and file paths
        """
        print("\n" + "="*70)
        print(f"BATCH PROCESSING: {len(items)} items")
        print("="*70)

        results = []

        for i, item in enumerate(items):
            print(f"\n[{i+1}/{len(items)}] {item.get('filename', f'item_{i}')}")

            output_path = self.generate_speech(
                text=item['text'],
                output_filename=item.get('filename', f'output_{i}.mp3'),
                language=item.get('language')
            )

            results.append({
                'filename': item.get('filename'),
                'success': output_path is not None,
                'path': output_path,
                'language': item.get('language')
            })

            # Brief pause between items
            if i < len(items) - 1:
                time.sleep(1)

        # Print summary
        print("\n" + "="*70)
        print("BATCH COMPLETE")
        print("="*70)
        success_count = sum(1 for r in results if r['success'])
        print(f"Total: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}")
        print("="*70 + "\n")

        return results

    def show_status(self):
        """Display current system status."""
        print(self.elevenlabs.get_status())
        print("\n" + "="*70)
        print("AZURE TTS STATUS")
        print("="*70)
        print(f"Region: {self.azure.region}")
        print(f"Supported languages: {', '.join(AZURE_VOICES.keys())}")
        print("="*70)

# Singleton instance for the narration system
_tts_instance: Optional[MultiProviderTTS] = None

def get_multi_provider_tts() -> MultiProviderTTS:
    """Get or create the MultiProviderTTS singleton instance."""
    global _tts_instance
    if _tts_instance is None:
        from utils.asset_directory_utils import get_exports_directory
        output_dir = os.path.join(get_exports_directory(), "narrations")
        
        _tts_instance = MultiProviderTTS(
            elevenlabs_accounts=ELEVENLABS_ACCOUNTS,
            azure_speech_key=AZURE_SPEECH_KEY,
            azure_region=AZURE_REGION,
            output_dir=output_dir
        )
    return _tts_instance    