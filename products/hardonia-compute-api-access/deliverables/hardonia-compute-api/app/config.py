from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "hardonia-compute-api"
    host: str = "127.0.0.1"
    port: int = 8050

    ollama_router_url: str = "http://127.0.0.1:11438"
    comfyui_url: str = "http://127.0.0.1:8188"
    audit_api_url: str = "http://127.0.0.1:8011"

    admin_key: str = "change-me-admin-key"
    db_path: str = "data/usage.db"
    redis_url: str = ""
    rate_limit_per_min: int = 30

    # Set DISABLE_DEMO_KEY=true in production to turn off the public demo key.
    disable_demo_key: bool = False

    # Restrict /admin/keys to loopback (defense in depth). Set false only behind a trusted proxy.
    admin_local_only: bool = True

    # Fixed demo key so the public playground works out of the box (Day-1 demo only)
    demo_key: str = "hk_demo_9f3c2a7b1e"


settings = Settings()
