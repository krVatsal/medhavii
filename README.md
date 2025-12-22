# मेधावी (Medhavi) - AI Presentation Generator for India

**Medhavi** (meaning "intelligent" or "wise" in Sanskrit) is an AI presentation generator with native multilingual support, regional context awareness, and voice narration in 11+ Indian languages.

## 🌟 Standout Features (Cherry on the Cake!)

### 🎙️ **Native Indian Voice Narration**
Generate presentations with natural-sounding voice narration in 11+ Indian languages using Bhashini API - making content accessible across India's linguistic diversity.

### 🇮🇳 **Regional Context Intelligence**
Unlike generic AI tools, Medhavi understands Indian context - references Delhi Metro, Mumbai Dabbawalas, Chennai IT Corridor, and other culturally relevant examples that resonate with Indian audiences.

### 🎬 **Animated Educational Videos**
Integrated Manim support for creating stunning mathematical and educational animations - transform complex concepts into engaging visual content.

### 🔄 **Multi-Provider AI Flexibility**
Switch between Google Gemini, OpenAI, Anthropic Claude, or run completely offline with Ollama - total control over your AI backend.

### 📄 **Intelligent Document Processing**
Upload existing PDFs or PowerPoints and let AI transform them into polished, narrated presentations while preserving key insights.

### 🎨 **Dynamic Image Generation**
Multiple image sources (DALL-E 3, Gemini Flash, Pexels, Pixabay) ensure your presentations are always visually stunning.

### 🛠️ **MCP Server Integration**
Model Context Protocol server enables seamless integration with AI agents and workflows - future-ready architecture.

### 🌐 **Web-Grounded Content**
Real-time web grounding ensures your presentations contain up-to-date, factually accurate information.

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
- Docker and Docker Compose
- Manim (for video animations)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd medhavii
```

### 2. Pull Manim Docker Image
Manim is required for generating animated video content. Pull the official image:
```bash
docker pull manimcommunity/manim
```

### 3. Environment Setup

**Backend Configuration:**
1. Navigate to `servers/fastapi/`
2. Create `.env` file with the following variables:
```bash
# User configuration
USER_CONFIG_PATH=./user_config.json
CAN_CHANGE_KEYS=true
APP_DATA_DIRECTORY=./app_data

# Bhashini TTS (Voice Narration)
BHASHINI_USER_ID=your_user_id
BHASHINI_API_KEY=your_api_key
```

3. Create `user_config.json`:
```json
{
  "LLM": "google",
  "GOOGLE_API_KEY": "your_google_api_key",
  "GOOGLE_MODEL": "models/gemini-2.0-flash",
  "IMAGE_PROVIDER": "gemini_flash",
  "WEB_GROUNDING": true
}
```

**Frontend Configuration:**
1. Navigate to `servers/nextjs/`
2. Install dependencies:
```bash
npm install
```

### 4. Running the Application

**Option A: Using Docker Compose (Recommended)**
```bash
docker-compose up --build
```
This will start:
- FastAPI backend on port 8000
- Next.js frontend on port 3000
- PostgreSQL database
- Redis cache (if configured)

**Option B: Running Separately**

Backend:
```bash
cd servers/fastapi
pip install -r requirements.txt
# or
pip install -e .
uvicorn api.main:app --reload --port 8000
```

Frontend:
```bash
cd servers/nextjs
npm install
npm run dev
```

Access the application at `http://localhost:3000`

## Implemented Features

### Core Features
- **Multilingual Support**: Generate presentations in 11+ Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, English)
- **Voice Narration**: Text-to-speech using Bhashini API with native language support
- **Regional Context**: Examples and references familiar to Indian audiences (Delhi Metro, Mumbai Dabbawalas, etc.)
- **Multiple LLM Providers**: Google Gemini, OpenAI GPT, Anthropic Claude, Ollama
- **Document Upload**: Generate presentations from PDF and PPTX files
- **Image Generation**: DALL-E 3, Gemini Flash, Pexels, Pixabay integration
- **Custom Templates**: HTML and Tailwind CSS based presentation templates
- **Export Options**: PPTX and PDF export formats
- **REST API**: Full API for programmatic access
- **MCP Server**: Model Context Protocol server for integration
- **Animated Videos**: Manim integration for creating educational video content

### Advanced Features
- Web grounding for real-time information
- Customizable tone (casual, professional, funny, educational, sales_pitch)
- Adjustable verbosity levels
- Template-based generation
- File upload and processing
- Quiz generation feature

## Technical Architecture

**Backend (FastAPI):**
- **Framework**: FastAPI with Python 3.11+
- **AI/LLM Integration**: Multi-provider support (Google Gemini, OpenAI, Anthropic, Ollama)
- **Document Processing**: PDF and PPTX parsing and analysis
- **Voice Synthesis**: Bhashini API integration for multilingual TTS
- **Image Processing**: Multiple image generation providers
- **Animation**: Manim for mathematical and educational video animations
- **Vector Database**: ChromaDB for document embeddings and semantic search
- **API Design**: RESTful API with OpenAPI/Swagger documentation
- **MCP Server**: LangGraph-based Model Context Protocol implementation

**Frontend (Next.js):**
- **Framework**: Next.js 14 with React
- **UI Components**: Tailwind CSS, shadcn/ui components
- **State Management**: Zustand store
- **API Communication**: Axios for HTTP requests
- **Presentation Editor**: HTML5 Canvas-based editor
- **File Upload**: Multi-file upload with progress tracking

**Infrastructure:**
- **Containerization**: Docker and Docker Compose
- **Database**: PostgreSQL for persistent storage
- **Caching**: Redis for performance optimization
- **Web Server**: Nginx for reverse proxy and static file serving

**Key Technologies:**
- Python-PPTX for PowerPoint generation
- PDF export using HTML to PDF conversion
- Real-time streaming for long-running operations
- Webhook support for event notifications
- Template engine for customizable presentation layouts

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

# Bhashini TTS (Voice Narration)
BHASHINI_USER_ID=your_user_id
BHASHINI_API_KEY=your_api_key
```

**User Config (user_config.json):**
```json
{
  "LLM": "google",
  "GOOGLE_API_KEY": "your_api_key",
  "GOOGLE_MODEL": "models/gemini-2.0-flash",
  "IMAGE_PROVIDER": "gemini_flash",
  "WEB_GROUNDING": true
}
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
