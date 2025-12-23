# मेधावी (Medhavi) - AI Presentation Generator for India

**Medhavi** (meaning "intelligent" or "wise" in Sanskrit) is an AI presentation generator with native multilingual support, regional context awareness, and voice narration in 11+ Indian languages.

**Key Features:**
- Voice Narration in Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, and English using Bhashini API
- Regional context with examples familiar to Indian audiences
- Multiple LLM support (Google Gemini, OpenAI, Anthropic, Ollama)
- Generate from documents (PDF, PPTX) or text prompts
- Export to PDF and PPTX formats

## Overview

Medhavi is an AI-powered presentation generator designed to assist users in creating engaging presentations in multiple Indian languages. It leverages advanced language models and regional context to provide a unique experience tailored for Indian audiences.

## Setup

To set up Medhavi, ensure you have the following prerequisites installed:
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional, for caching)

To pull the latest version of Manim, run:
```bash
git clone https://github.com/3b1b/manim.git
```

## Implemented Features

- Voice Narration in 11+ Indian languages
- Regional context with examples familiar to Indian audiences
- Multiple LLM support
- Document generation from PDF and PPTX
- Export options for PDF and PPTX formats

## Technical Explanation

Medhavi utilizes various language models to generate presentations based on user input. It supports voice narration through the Bhashini API and provides REST API endpoints for integration with other applications.

### API Usage

**Endpoint:** `POST /api/v1/ppt/presentation/generate`

**Request:**
```json
{
  "content": "Introduction to Machine Learning",
  "n_slides": 5,
  "language": "English",
  "template": "general",
  "export_as": "pptx"
}
```

**Response:**
```json
{
  "presentation_id": "d3000f96-096c-4768-b67b-e99aed029b57",
  "path": "/app_data/d3000f96-096c-4768-b67b-e99aed029b57/Introduction_to_Machine_Learning.pptx",
  "edit_path": "/presentation?id=d3000f96-096c-4768-b67b-e99aed029b57"
}
```

**Key Parameters:**
- `content`: Topic or content for presentation (required)
- `n_slides`: Number of slides (default: 8)
- `language`: Target language (default: "English")
- `tone`: casual, professional, funny, educational, sales_pitch
- `export_as`: pptx or pdf
- `files`: Upload files via `/api/v1/ppt/files/upload`

## License

Apache 2.0


## Features

**Multilingual & Regional**
- 11+ Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, English)
- Voice narration using Bhashini API
- Regional context and examples (Delhi Metro, Mumbai Dabbawalas, Chennai IT Corridor, etc.)

**AI & Generation**
- Multiple LLM providers: Google Gemini, OpenAI, Anthropic Claude, Ollama
- Generate from prompts or documents (PDF, PPTX)
- Image generation: DALL-E 3, Gemini Flash, Pexels, Pixabay
- Custom templates with HTML and Tailwind CSS

**Export & Integration**
- Export to PPTX and PDF
- REST API for integration
- Model Context Protocol (MCP) server

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional, for caching)

## API Usage

### Generate Presentation

**Endpoint:** `POST /api/v1/ppt/presentation/generate`

**Request:**
```json
{
  "content": "Introduction to Machine Learning",
  "n_slides": 5,
  "language": "English",
  "template": "general",
  "export_as": "pptx"
}
```

**Response:**
```json
{
  "presentation_id": "d3000f96-096c-4768-b67b-e99aed029b57",
  "path": "/app_data/d3000f96-096c-4768-b67b-e99aed029b57/Introduction_to_Machine_Learning.pptx",
  "edit_path": "/presentation?id=d3000f96-096c-4768-b67b-e99aed029b57"
}
```

**Key Parameters:**
- `content`: Topic or content for presentation (required)
- `n_slides`: Number of slides (default: 8)
- `language`: Target language (default: "English")
- `tone`: casual, professional, funny, educational, sales_pitch
- `export_as`: pptx or pdf
- `files`: Upload files via `/api/v1/ppt/files/upload`

## Configuration

### Environment Variables

**Backend (.env in servers/fastapi/):**
```bash
# User configuration
USER_CONFIG_PATH=path/to/user_config.json
CAN_CHANGE_KEYS=true
APP_DATA_DIRECTORY=path/to/app_data

```



**Supported LLM Providers:**
- `google` - Google Gemini
- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude
- `ollama` - Local Ollama models

**Image Providers:**
- `gemini_flash` - Google Gemini (requires GOOGLE_API_KEY)
- `dall-e-3` - OpenAI DALL-E (requires OPENAI_API_KEY)
- `pexels` - Pexels stock photos (requires PEXELS_API_KEY)
- `pixabay` - Pixabay stock photos (requires PIXABAY_API_KEY)

## Documentation

- [Voice Narration Guide](VOICE_NARRATION_GUIDE.md)
- [Regional References Guide](REGIONAL_REFERENCES_GUIDE.md)
- [Quiz Feature Documentation](QUIZ_FEATURE.md)
- [Project Documentation](PROJECT_DOCUMENTATION.md)

## License

Apache 2.0
