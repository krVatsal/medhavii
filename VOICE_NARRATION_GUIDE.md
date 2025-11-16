# Voice Narration Feature - Implementation Guide

## Overview

The voice narration feature adds AI-powered teaching-style audio explanations to presentations using the Bhashini API for native language text-to-speech. This feature generates detailed, educational narrations that go beyond simple text-to-speech by including examples, regional references, and student-friendly explanations.

## Architecture

### Backend Components

#### 1. Models (`models/voice_narration_models.py`)
- `TeachingScript`: Contains teaching explanation, duration, and key concepts
- `VoiceNarrationRequest`: Request parameters for narration generation
- `SlideNarration`: Generated narration data for a single slide
- `PresentationNarration`: Complete narration for all slides
- `BhashiniTTSRequest/Response`: Bhashini API integration models

#### 2. Services

**Teaching Script Generator** (`services/teaching_script_generator.py`)
- Generates detailed teaching explanations using LLM
- Extracts slide content recursively
- Creates student-level appropriate content (beginner/intermediate/advanced)
- Adds regional references and real-world examples
- Estimates narration duration

**Bhashini TTS Service** (`services/bhashini_tts_service.py`)
- Integrates with Bhashini API for text-to-speech
- Supports 11 Indian languages + English
- Handles audio file generation and storage
- Manages batch speech generation
- Caches audio files in organized directory structure

#### 3. API Endpoints (`api/v1/ppt/endpoints/narration.py`)

**POST `/api/v1/ppt/narration/generate`**
- Generates complete narration for all slides
- Parameters: presentation_id, language_code, voice_gender, student_level, include_regional_references
- Returns: PresentationNarration with audio URLs and scripts

**POST `/api/v1/ppt/narration/regenerate-slide`**
- Regenerates narration for a single slide
- Useful for iterative improvements

**GET `/api/v1/ppt/narration/supported-languages`**
- Returns list of supported languages

### Frontend Components

#### 1. Models (`models/narration.ts`)
TypeScript interfaces mirroring backend models

#### 2. API Service (`services/api/narration-api.ts`)
- `NarrationApi.generatePresentationNarration()`: Generate full narration
- `NarrationApi.regenerateSlideNarration()`: Regenerate single slide
- `NarrationApi.getSupportedLanguages()`: Fetch supported languages

#### 3. React Components

**`useNarration` Hook** (`presentation/hooks/useNarration.ts`)
- Manages audio playback state
- Handles auto-advance to next slide
- Controls playback speed
- Tracks audio progress
- Auto-plays narration when slide changes (if enabled)

**`NarrationControls`** (`components/NarrationControls.tsx`)
- Audio player controls (play/pause, seek, speed control)
- Auto-advance toggle
- Narration script viewer
- Progress bar with time display

**`GenerateNarrationButton`** (`presentation/components/GenerateNarrationButton.tsx`)
- Dialog for narration generation settings
- Language selection (11 Indian languages + English)
- Voice gender selection
- Student level selection
- Regional references toggle

**`PresentationMode`** (updated)
- Integrated audio player
- Narration controls overlay
- Auto-advance functionality
- Hidden audio element for playback

## Setup Requirements

### Environment Variables

Add to `servers/fastapi/.env`:
```env
BHASHINI_USER_ID=your_user_id
BHASHINI_API_KEY=your_api_key
BHASHINI_PIPELINE_ID=your_pipeline_id
```

### Directory Structure
```
exports/
  narrations/
    hi/         # Hindi audio files
    bn/         # Bengali audio files
    ta/         # Tamil audio files
    ...
```

## Supported Languages

1. Hindi (hi)
2. Bengali (bn)
3. Tamil (ta)
4. Telugu (te)
5. Marathi (mr)
6. Gujarati (gu)
7. Kannada (kn)
8. Malayalam (ml)
9. Punjabi (pa)
10. Odia (or)
11. English (en)

## User Workflow

### Generating Narration

1. **Open Presentation Editor**
   - Navigate to presentation edit page
   
2. **Click "Generate Voice Narration" Button**
   - Located in the header toolbar
   
3. **Configure Settings**
   - Select target language
   - Choose voice gender (male/female)
   - Set student level (beginner/intermediate/advanced)
   - Enable/disable regional references
   
4. **Generate**
   - System generates teaching scripts for all slides using LLM
   - Converts scripts to speech using Bhashini
   - Stores audio files and returns URLs
   - Shows progress toast notification

### Using Narration in Presentation Mode

1. **Enter Presentation Mode**
   - Click "Present" button
   
2. **Narration Controls Appear**
   - Bottom overlay with player controls
   - Play/Pause button
   - Progress slider
   - Playback speed control (0.5x - 2x)
   - Auto-advance toggle
   
3. **Auto-Advance Feature**
   - Enable auto-advance
   - Narration plays automatically for current slide
   - Advances to next slide when audio ends
   - Continues until presentation end

### Keyboard Shortcuts (Presentation Mode)
- **Space/Arrow Keys**: Manual slide navigation
- **F**: Toggle fullscreen
- **Escape**: Exit presentation mode

## Technical Details

### LLM Teaching Script Generation

The system uses the configured LLM to generate teaching-style explanations:

**System Prompt**: Instructs the model to act as an expert teacher creating audio narration scripts

**User Prompt**: Includes:
- Slide content
- Speaker notes (if available)
- Presentation context
- Student level requirement
- Regional reference requirement

**Output**: JSON with:
- Teaching explanation (detailed script)
- Estimated duration
- Key concepts covered

### Bhashini API Integration

**Request Format**:
```json
{
  "pipelineTasks": [{
    "taskType": "tts",
    "config": {
      "language": {"sourceLanguage": "hi"},
      "serviceId": "",
      "gender": "female",
      "samplingRate": 8000
    }
  }],
  "inputData": {
    "input": [{"source": "text to convert"}]
  }
}
```

**Response**: Base64 encoded audio content (WAV format)

**Storage**: 
- Audio files saved to `exports/narrations/{language_code}/{uuid}.wav`
- URL pattern: `/exports/narrations/{language_code}/{filename}.wav`

### Audio Playback

**HTML5 Audio Element**:
- Hidden in PresentationMode
- Preloads next slide audio
- Event listeners for progress tracking
- Playback rate control (0.5x to 2x)

**Auto-Advance Logic**:
```
1. Audio loads when slide changes
2. Auto-play if enabled
3. Track audio ended event
4. Advance to next slide
5. Repeat until last slide
```

## API Examples

### Generate Full Presentation Narration

**Request**:
```typescript
const narration = await NarrationApi.generatePresentationNarration({
  presentation_id: "uuid-here",
  language_code: "hi",
  voice_gender: "female",
  student_level: "intermediate",
  include_regional_references: true
});
```

**Response**:
```json
{
  "presentation_id": "uuid",
  "slides": [
    {
      "slide_index": 0,
      "script": "Namaste! Aaj hum...",
      "audio_url": "/exports/narrations/hi/abc123.wav",
      "duration_seconds": 45.5,
      "language": "hi"
    }
  ],
  "total_duration_seconds": 450.0,
  "language": "hi",
  "created_at": "2025-11-13T00:00:00"
}
```

### Regenerate Single Slide

**Request**:
```typescript
const slideNarration = await NarrationApi.regenerateSlideNarration({
  presentation_id: "uuid",
  slide_index: 2,
  language_code: "hi",
  voice_gender: "male",
  student_level: "beginner",
  include_regional_references: true
});
```

## Testing Checklist

- [ ] Backend API endpoints respond correctly
- [ ] LLM generates appropriate teaching scripts
- [ ] Bhashini TTS produces clear audio
- [ ] Audio files are stored correctly
- [ ] Frontend fetches narration data
- [ ] Audio player controls work (play/pause/seek/speed)
- [ ] Auto-advance advances slides correctly
- [ ] Multiple languages work
- [ ] Regenerate single slide works
- [ ] Error handling displays appropriate messages

## Known Limitations

1. **Bhashini API Rate Limits**: May need throttling for large presentations
2. **Audio File Size**: WAV files can be large; consider MP3 conversion
3. **LLM Context**: Very long slides may need chunking
4. **Browser Support**: Requires HTML5 audio support
5. **Network**: Audio streaming requires stable connection

## Future Enhancements

1. **Background Music**: Add optional background music
2. **Voice Customization**: Pitch, tone adjustments
3. **Pause Points**: Manual pause points in narration
4. **Subtitles**: Real-time subtitle display
5. **Export with Audio**: Download presentation with embedded narration
6. **Offline Mode**: Cache audio for offline playback
7. **Voice Cloning**: Custom voice options
8. **Multi-Speaker**: Different voices for different sections

## Troubleshooting

### Audio Not Playing
- Check browser console for errors
- Verify audio URL is accessible
- Check Bhashini API credentials
- Ensure exports directory has write permissions

### Generation Fails
- Verify LLM is configured and accessible
- Check Bhashini API key validity
- Ensure presentation has slides
- Check server logs for detailed errors

### Auto-Advance Not Working
- Verify narration data is loaded
- Check audio "ended" event listener
- Ensure auto-advance toggle is enabled
- Verify slide count matches narration count

## Performance Optimization

1. **Lazy Loading**: Load audio only when needed
2. **Caching**: Cache generated narrations in database
3. **Streaming**: Stream audio instead of full download
4. **Compression**: Convert WAV to MP3 for smaller size
5. **Parallel Generation**: Generate multiple narrations concurrently
6. **CDN**: Serve audio files from CDN for better performance

## Security Considerations

1. **API Keys**: Store Bhashini credentials securely
2. **File Access**: Restrict audio file access to authorized users
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Prevent API abuse
5. **File Cleanup**: Implement cleanup for old audio files
