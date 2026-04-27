from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UNBAKE_", env_file=".env", extra="ignore")

    env: str = "dev"
    tmp_dir: str = "./tmp"
    max_audio_duration_sec: int = 600
    transcriber_model: str = "large-v3"
    transcriber_device: str = "cuda"
    transcriber_compute_type: str = "float16"
    batch_size: int = 16
    catalog_base_url: str = "https://lrclib.net"
    gpu_price_per_second: float = 0.00016


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
