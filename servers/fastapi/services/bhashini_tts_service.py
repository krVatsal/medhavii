"""
Service to interact with Bhashini API for text-to-speech with translation
Simple flow: auth() → translate() → tts()
"""
import base64
import os
import uuid
import httpx
from typing import Optional
from utils.asset_directory_utils import get_exports_directory


class BhashiniTTSService:
    """Service to generate speech from text using Bhashini API with translation"""
    
    def __init__(self):
        self.user_id = os.getenv("BHASHINI_USER_ID", "")
        self.ulca_api_key = os.getenv("BHASHINI_ULCA_API_KEY", "")
        self.pipeline_id = os.getenv("BHASHINI_PIPELINE_ID", "")
        self.audio_dir = os.path.join(get_exports_directory(), "narrations")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        if not self.user_id or not self.ulca_api_key or not self.pipeline_id:
            print("Warning: BHASHINI_USER_ID, BHASHINI_ULCA_API_KEY, or BHASHINI_PIPELINE_ID not set.")
    
    async def _get_pipeline_config(self, source_lang: str, target_lang: str) -> dict:
        """
        Step 1: Get pipeline configuration (auth)
        """
        url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
        
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                },
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": target_lang
                        }
                    }
                }
            ],
            "pipelineRequestConfig": {
                "pipelineId": self.pipeline_id
            }
        }
        
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.ulca_api_key
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"Bhashini config failed: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            return response.json()

    async def translate(self, text: str, source_lang: str, target_lang: str, config: dict) -> str:
        """
        Step 2: Translate text using config
        """
        # Extract translation config
        pipeline_response = config.get("pipelineResponseConfig", [])
        trans_task = next((t for t in pipeline_response if t["taskType"] == "translation"), None)
        
        if not trans_task:
            raise ValueError("No translation task in pipeline config")
            
        trans_config = trans_task["config"][0]
        service_id = trans_config["serviceId"]
        inference_url = trans_config["inferenceEndPoint"]["callbackUrl"]
        api_key = trans_config["inferenceEndPoint"]["inferenceApiKey"]["value"]
        
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        },
                        "serviceId": service_id
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
            "Authorization": api_key
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(inference_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"Translation failed: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            result = response.json()
            translated_text = result.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("target", "")
            return translated_text
    
    async def tts(self, text: str, language_code: str, gender: str, config: dict) -> str:
        """
        Step 3: Generate TTS using config
        """
        # Extract TTS config
        pipeline_response = config.get("pipelineResponseConfig", [])
        tts_task = next((t for t in pipeline_response if t["taskType"] == "tts"), None)
        
        if not tts_task:
            raise ValueError("No TTS task in pipeline config")
            
        tts_config = tts_task["config"][0]
        service_id = tts_config["serviceId"]
        inference_url = tts_config["inferenceEndPoint"]["callbackUrl"]
        api_key = tts_config["inferenceEndPoint"]["inferenceApiKey"]["value"]
        
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": language_code
                        },
                        "serviceId": service_id,
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
            "Authorization": api_key
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(inference_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"TTS failed: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            result = response.json()
            audio_base64 = result.get("pipelineResponse", [{}])[0].get("audio", [{}])[0].get("audioContent", "")
            return audio_base64
    
    async def generate_speech(
        self,
        text: str,
        language_code: str = "hi",
        gender: str = "female",
        source_lang: str = "en"
    ) -> tuple[str, str]:
        """
        Complete flow: Get config -> Translate (if needed) -> TTS
        """
        try:
            # Step 1: Get pipeline config
            print(f"[Bhashini] Getting pipeline config for {source_lang} -> {language_code}...")
            config = await self._get_pipeline_config(source_lang, language_code)
            
            # Step 2: Translate if source != target
            translated_text = text
            if source_lang != language_code:
                print(f"[Bhashini] Translating: {source_lang} → {language_code}")
                translated_text = await self.translate(text, source_lang, language_code, config)
                print(f"[Bhashini] Translated: {translated_text[:100]}...")
            
            # Step 3: Generate TTS
            print(f"[Bhashini] Generating TTS...")
            audio_base64 = await self.tts(translated_text, language_code, gender, config)
            
            if not audio_base64:
                raise ValueError("No audio content in Bhashini response")
            
            # Save audio to file
            audio_file_path, audio_url = await self._save_audio_file(audio_base64, language_code)
            
            return audio_file_path, audio_url
                
        except Exception as e:
            print(f"[Bhashini] Error: {e}")
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
        gender: str = "female",
        source_lang: str = "en"
    ) -> list[tuple[str, str]]:
        """
        Generate speech for multiple texts
        
        Args:
            texts: List of texts to convert
            language_code: Target language code
            gender: Voice gender
            source_lang: Source language of input texts
        
        Returns:
            List of tuples (file_path, audio_url)
        """
        results = []
        
        for text in texts:
            try:
                file_path, audio_url = await self.generate_speech(text, language_code, gender, source_lang)
                results.append((file_path, audio_url))
            except Exception as e:
                print(f"Error generating speech for text: {text[:50]}... Error: {e}")
                results.append(("", ""))
        
        return results
    
    def get_supported_languages(self) -> dict[str, str]:
        """Get supported language codes"""
        return {
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


# Singleton instance
_bhashini_service: Optional[BhashiniTTSService] = None


def get_bhashini_service() -> BhashiniTTSService:
    """Get or create Bhashini TTS service instance"""
    global _bhashini_service
    if _bhashini_service is None:
        _bhashini_service = BhashiniTTSService()
    return _bhashini_service
