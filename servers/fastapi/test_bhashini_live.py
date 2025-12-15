import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.bhashini_tts_service import BhashiniTTSService

# Load env vars from .env file
load_dotenv()

# Remove proxy settings if they exist
for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if key in os.environ:
        del os.environ[key]
        print(f"Removed {key} from environment variables")

async def main():
    print("="*50)
    print("Testing Bhashini TTS Service Integration (Live API)")
    print("="*50)
    
    # Check credentials
    user_id = os.getenv("BHASHINI_USER_ID")
    ulca_key = os.getenv("BHASHINI_UDYAT_KEY") or os.getenv("BHASHINI_ULCA_API_KEY")
    pipeline_id = os.getenv("BHASHINI_PIPELINE_ID")
    
    print(f"BHASHINI_USER_ID present: {'Yes' if user_id else 'No'}")
    print(f"BHASHINI_UDYAT_KEY present: {'Yes' if ulca_key else 'No'}")
    print(f"BHASHINI_PIPELINE_ID present: {'Yes' if pipeline_id else 'No'}")
    
    if not (user_id and ulca_key and pipeline_id):
        print("\n❌ Missing credentials in .env file. Please add them and try again.")
        return

    try:
        service = BhashiniTTSService()
        
        text = "Hello, this is a test of the Bhashini text to speech service."
        target_lang = "hi" # Hindi
        
        print(f"\nInput Text: '{text}'")
        print(f"Source Language: en")
        print(f"Target Language: {target_lang}")
        
        print("\n--- Starting Process ---")
        
        # 1. Test generate_speech (which does Auth -> Translate -> TTS)
        file_path, url = await service.generate_speech(
            text=text,
            language_code=target_lang,
            source_lang="en"
        )
        
        print("\n✅ Success!")
        print(f"Generated Audio File: {file_path}")
        print(f"Audio URL: {url}")
        
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            print(f"File Size: {size_kb:.2f} KB")
            print("\nYou can play this file to verify the audio.")
        else:
            print("❌ File was not created on disk")

    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
