from typing import Literal

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    # ========================================
    # APPLICATION METADATA
    # ========================================
    PROJECT_NAME: str = Field(default="sahiloan-chatbot", description="Project identifier")

    COMET_PROJECT: str = Field(default="sahiloan-chatbot", description="Project identifier")

    ENVIRONMENT: Literal["local", "development", "staging", "production"] = Field(
        default="local", description="Deployment environment"
    )

    COMET_TRACING: bool = Field(default=False, description="Enable Comet tracing")

    APP_VERSION: str = Field(default="0.0.1", pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")

    DEBUG: bool = Field(default=False, description="Debug mode (auto-disabled in production)")

    # ========================================
    # API KEYS (REQUIRED - NO DEFAULTS)
    # ========================================
    OPENAI_API_KEY: SecretStr = Field(..., min_length=10, description="OpenAI API key (required)")

    GEMINI_API_KEY1: SecretStr = Field(..., min_length=10, description="Gemini API key (required)")

    GEMINI_API_KEY2: SecretStr = Field(..., min_length=10, description="Gemini API key (required)")

    GEMINI_API_KEY3: SecretStr = Field(..., min_length=10, description="Gemini API key (required)")

    GROQ_API_KEY1: SecretStr = Field(..., min_length=10, description="Groq API key (required)")
    GROQ_API_KEY2: SecretStr = Field(..., min_length=10, description="Groq API key (required)")
    GROQ_API_KEY3: SecretStr = Field(..., min_length=10, description="Groq API key (required)")

    COMET_API_KEY: SecretStr = Field(..., min_length=10, description="Comet API key (required)")

    ELEVENLABS_API_KEY: SecretStr = Field(..., min_length=10, description="ElevenLabs API key (required)")

    # ========================================
    # MODEL CONFIGURATIONS
    # ========================================

    GPT_4_1_NANO_MODEL: str = Field(default="gpt-4.1-nano", description="GPT 4.1 Nano model identifier")
    GPT_4O_MINI_MODEL: str = Field(default="gpt-4o-mini", description="GPT 4o Mini model identifier")
    GPT_5_NANO_MODEL: str = Field(default="gpt-5-nano", description="GPT 5 Nano model identifier")
    GEMINI_2_5_FLASH_LITE_MODEL: str = Field(
        default="gemini-2.5-flash-lite", description="Gemini 2.5 Flash Lite model identifier"
    )

    GEMINI_2_5_FLASH_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini 2.5 Flash model identifier")

    QWEN_3_32B_MODEL: str = Field(default="qwen/qwen3-32b", description="Qwen 3.3 32b model identifier")

    LLAMA_3_3_70B_MODEL: str = Field(
        default="llama-3.3-70b-versatile", description="Groq Llama 3.3 70b Versatile model identifier"
    )

    LLAMA_3_1_8B_MODEL: str = Field(default="llama-3.1-8b-instant", description="Groq Llama 3.1 8b model identifier")

    CLAUDE_3_5_SONNET_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022", description="Claude 3.5 Sonnet model identifier"
    )

    # ========================================
    # OBSERVABILITY SETTINGS
    # ========================================
    COMET_ENDPOINT: HttpUrl = Field(default="https://www.comet.com", description="Comet API endpoint")

    COMET_WORKSPACE: str = Field(..., description="Comet workspace name")

    COMET_URL_OVERRIDE: str = Field(default="https://www.comet.com/opik/api", description="Comet API URL override")

    # ========================================
    # DATABASE SETTINGS
    # ========================================
    POSTGRES_URL: str = Field(..., description="PostgreSQL URI")

    PINECONE_API_KEY: SecretStr = Field(..., min_length=10, description="Pinecone API key (required)")
    PINECONE_INDEX_NAME: str = Field(default="sahiloan", description="Pinecone index name")

    # ========================================
    # EMBEDDING SETTINGS
    # ========================================
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    EMBEDDING_DIMENSIONS: int = Field(default=1024, description="Embedding dimensions")


settings = Settings()
