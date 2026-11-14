import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "PAYGUARD"
    APP_VERSION: str = "0.2.0"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database
    DATABASE_PATH: str = "backend/payguard.db"

    # LLM Gateway Configuration
    LLM_PROVIDER: str = "mock"  # mock, openai, anthropic, gemini, groq, ollama
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_TIMEOUT_SECONDS: float = 10.0
    LLM_TEMPERATURE: float = 0.0

    # Multi-Agent Flags
    ENABLE_MULTI_AGENT: bool = True
    INTENT_AGENT_ENABLED: bool = True
    BEHAVIOURAL_AGENT_ENABLED: bool = True
    SECURITY_INTEL_AGENT_ENABLED: bool = True
    AUDIT_AGENT_ENABLED: bool = True

    # Policy Defaults
    DEFAULT_MAX_TX_AMOUNT: float = 50.0
    DEFAULT_DAILY_LIMIT: float = 200.0
    DEFAULT_HIGH_RISK_THRESHOLD: int = 70
    DEFAULT_MEDIUM_RISK_THRESHOLD: int = 30
    DUPLICATE_WINDOW_SECONDS: int = 120

    # Blockchain & Cryptographic Signer Configuration
    NEAR_NETWORK: str = "testnet"
    NEAR_NODE_URL: str = "https://rpc.testnet.near.org"
    NEAR_CONTRACT_ID: str = "payguard-vault.testnet"
    POLICY_SIGNER_PRIVATE_KEY: Optional[str] = None
    POLICY_SIGNER_PUBLIC_KEY: Optional[str] = None
    ALLOW_EPHEMERAL_SIGNER_KEY: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
