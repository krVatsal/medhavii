"""
Service to interact with Bhashini API for text-to-speech
"""
import base64
import os
import uuid
import httpx
from typing import Optional
from models.voice_narration_models import BhashiniTTSRequest, BhashiniTTSResponse
from utils.asset_directory_utils import get_exports_directory


# Bhashini API configuration
BHASHINI_API_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_PIPELINE_ID = os.getenv("BHASHINI_PIPELINE_ID", "")

# Language code mapping for Bhashini
LANGUAGE_CODES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "en": "English"
}


class BhashiniTTSService:
    """Service to generate speech from text using Bhashini API"""
    
    def __init__(self):
        self.api_url = BHASHINI_API_URL
        self.user_id = BHASHINI_USER_ID
        self.api_key = BHASHINI_API_KEY
        self.pipeline_id = BHASHINI_PIPELINE_ID
        self.audio_dir = os.path.join(get_exports_directory(), "narrations")
        os.makedirs(self.audio_dir, exist_ok=True)
    
    async def generate_speech(
        self,
        text: str,
        language_code: str = "hi",
        gender: str = "female"
    ) -> tuple[str, str]:
        """
        Generate speech from text using Bhashini API
        
        Args:
            text: Text to convert to speech
            language_code: Language code (hi, bn, ta, etc.)
            gender: Voice gender (male/female)
        
        Returns:
            Tuple of (audio_file_path, audio_url)
        """
        
        # Prepare the request payload for Bhashini
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": language_code
                        },
                        "serviceId": "",
                        "gender": gender,
                        "samplingRate": 8000
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract audio content from response
                audio_content = result.get("pipelineResponse", [{}])[0].get("audio", [{}])[0].get("audioContent", "")
                
                if not audio_content:
                    raise ValueError("No audio content in Bhashini response")
                
                # Save audio to file
                audio_file_path, audio_url = await self._save_audio_file(audio_content, language_code)
                
                return audio_file_path, audio_url
                
        except httpx.HTTPError as e:
            print(f"Bhashini API error: {e}")
            raise Exception(f"Failed to generate speech: {str(e)}")
        except Exception as e:
            print(f"Error generating speech: {e}")
            raise
    
    async def _save_audio_file(self, base64_audio: str, language_code: str) -> tuple[str, str]:
        """
        Save base64 encoded audio to file
        
        Args:
            base64_audio: Base64 encoded audio content
            language_code: Language code for organizing files
        
        Returns:
            Tuple of (file_path, audio_url)
        """
        # Create language-specific subdirectory
        lang_dir = os.path.join(self.audio_dir, language_code)
        os.makedirs(lang_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join(lang_dir, filename)
        
        # Decode and save audio
        try:
            audio_bytes = base64.b64decode(base64_audio)
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            
            # Generate URL (relative to exports directory)
            audio_url = f"/exports/narrations/{language_code}/{filename}"
            
            return file_path, audio_url
            
        except Exception as e:
            print(f"Error saving audio file: {e}")
            raise
    
    async def generate_batch_speech(
        self,
        texts: list[str],
        language_code: str = "hi",
        gender: str = "female"
    ) -> list[tuple[str, str]]:
        """
        Generate speech for multiple texts
        
        Args:
            texts: List of texts to convert
            language_code: Language code
            gender: Voice gender
        
        Returns:
            List of tuples (file_path, audio_url)
        """
        results = []
        
        for text in texts:
            try:
                file_path, audio_url = await self.generate_speech(text, language_code, gender)
                results.append((file_path, audio_url))
            except Exception as e:
                print(f"Error generating speech for text: {text[:50]}... Error: {e}")
                # Add empty result to maintain order
                results.append(("", ""))
        
        return results
    
    def get_supported_languages(self) -> dict[str, str]:
        """Get supported language codes and names"""
        return LANGUAGE_CODES.copy()


# Singleton instance
_bhashini_service: Optional[BhashiniTTSService] = None


def get_bhashini_service() -> BhashiniTTSService:
    """Get or create Bhashini TTS service instance"""
    global _bhashini_service
    if _bhashini_service is None:
        _bhashini_service = BhashiniTTSService()
    return _bhashini_service
