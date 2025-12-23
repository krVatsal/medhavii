"""
Unified TTS Service Manager
Routes TTS requests to appropriate service based on language and configuration
"""
from typing import Optional, Tuple
from enum import Enum
from services.gemini_tts_service import GeminiTTSService
from services.bhashini_tts_service import BhashiniTTSService


class TTSProvider(str, Enum):
    """Available TTS providers"""
    GEMINI = "gemini"
    BHASHINI = "bhashini"
    AZURE_ELEVENLABS = "azure_elevenlabs"  # Multi-provider TTS (Azure + ElevenLabs)


class UnifiedTTSService:
    """
    Manages multiple TTS services and routes requests appropriately
    """
    
    def __init__(self, default_provider: TTSProvider = TTSProvider.AZURE_ELEVENLABS):
        self.default_provider = default_provider
        self.gemini_service = None
        self.bhashini_service = None
        self.multi_provider_service = None
        
        # Language to provider mapping
        # Prefer Azure+ElevenLabs for all Indian languages
        self.language_provider_map = {
            # Indian languages - use Azure+ElevenLabs multi-provider
            "hi": TTSProvider.AZURE_ELEVENLABS,  # Hindi
            "bn": TTSProvider.AZURE_ELEVENLABS,  # Bengali
            "ta": TTSProvider.AZURE_ELEVENLABS,  # Tamil
            "te": TTSProvider.AZURE_ELEVENLABS,  # Telugu
            "mr": TTSProvider.AZURE_ELEVENLABS,  # Marathi
            "gu": TTSProvider.AZURE_ELEVENLABS,  # Gujarati
            "kn": TTSProvider.AZURE_ELEVENLABS,  # Kannada
            "ml": TTSProvider.AZURE_ELEVENLABS,  # Malayalam
            "pa": TTSProvider.AZURE_ELEVENLABS,  # Punjabi
            "or": TTSProvider.AZURE_ELEVENLABS,  # Odia
            "ur": TTSProvider.AZURE_ELEVENLABS,  # Urdu
            
            # English - use Azure+ElevenLabs
            "en": TTSProvider.AZURE_ELEVENLABS,
        }
    
    def _get_service(self, provider: TTSProvider):
        """Get or initialize the requested TTS service"""
        if provider == TTSProvider.GEMINI:
            if not self.gemini_service:
                self.gemini_service = GeminiTTSService()
            return self.gemini_service
        
        elif provider == TTSProvider.BHASHINI:
            if not self.bhashini_service:
                self.bhashini_service = BhashiniTTSService()
            return self.bhashini_service
        
        elif provider == TTSProvider.AZURE_ELEVENLABS:
            if not self.multi_provider_service:
                from services.tts import get_multi_provider_tts
                self.multi_provider_service = get_multi_provider_tts()
            return self.multi_provider_service
        
        raise ValueError(f"Unknown provider: {provider}")
    
    def get_provider_for_language(self, language_code: str) -> TTSProvider:
        """Determine which provider to use for a given language"""
        return self.language_provider_map.get(
            language_code,
            self.default_provider
        )
    
    async def generate_speech(
        self,
        text: str,
        language_code: str = "en",
        gender: str = "female",
        source_lang: str = "en",
        provider: Optional[TTSProvider] = None
    ) -> Tuple[str, str]:
        """
        Generate speech using the appropriate TTS service
        
        Args:
            text: Text to convert to speech
            language_code: Target language code
            gender: Voice gender preference
            source_lang: Source language for translation (if needed)
            provider: Force specific provider (optional)
        
        Returns:
            Tuple of (file_path, audio_url)
        """
        # Determine provider
        if provider is None:
            provider = self.get_provider_for_language(language_code)
        
        print(f"[TTS Manager] Using {provider.value} for language: {language_code}")
        
        # Get the service
        service = self._get_service(provider)
        
        # Generate speech based on provider type
        if provider == TTSProvider.GEMINI:
            return await service.generate_speech(
                text=text,
                language_code=language_code,
                gender=gender
            )
        
        elif provider == TTSProvider.BHASHINI:
            # Bhashini requires translation from source to target
            return await service.generate_speech(
                text=text,
                source_lang=source_lang,
                target_lang=language_code,
                gender=gender
            )
        
        elif provider == TTSProvider.AZURE_ELEVENLABS:
            # Multi-provider TTS with intelligent routing (synchronous)
            # Run in thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Generate filename
            import uuid
            filename = f"narration_{uuid.uuid4()}.mp3"
            
            # Generate speech in thread pool (it's synchronous)
            file_path = await loop.run_in_executor(
                None,
                service.generate_speech,
                text,
                filename,
                language_code
            )
            
            if file_path:
                # Convert file path to URL
                import os
                from utils.asset_directory_utils import get_exports_directory
                exports_dir = get_exports_directory()
                audio_url = f"/app_data/exports/narrations/{os.path.basename(file_path)}"
                return (file_path, audio_url)
            else:
                raise Exception("Failed to generate speech with Azure+ElevenLabs")
        
        raise ValueError(f"Unhandled provider: {provider}")
    
    def get_supported_languages(self, provider: Optional[TTSProvider] = None):
        """Get supported languages for a provider or all providers"""
        if provider:
            service = self._get_service(provider)
            return service.get_supported_languages()
        
        # Return combined list from all providers
        all_languages = set()
        
        # Get from each initialized service
        if self.gemini_service:
            all_languages.update(self.gemini_service.get_supported_languages())
        
        if self.bhashini_service:
            all_languages.update(self.bhashini_service.get_supported_languages())
        
        # Add languages from mapping
        all_languages.update(self.language_provider_map.keys())
        
        return list(all_languages)


# Singleton instance
_unified_tts_service: Optional[UnifiedTTSService] = None


def get_unified_tts_service() -> UnifiedTTSService:
    """Get or create the unified TTS service singleton"""
    global _unified_tts_service
    if _unified_tts_service is None:
        _unified_tts_service = UnifiedTTSService()
    return _unified_tts_service
