from enum import Enum


class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GROQ = "groq"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"
