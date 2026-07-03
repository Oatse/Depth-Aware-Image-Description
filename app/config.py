from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Depth-Aware Image Description"
    app_env: str = "development"
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")

    lm_studio_url: str = "http://localhost:1234"
    lm_studio_model: str = "gemma-4-e4b-it"
    lm_studio_timeout: int = 60
    lm_studio_health_timeout: float = 2.0
    gemma_mock: bool = False

    enable_depth_estimation: bool = True
    depth_model_path: Path = Path("./model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf")
    depth_input_size: int = 518
    depth_mock: bool = False

    max_image_size_mb: int = 5
    image_max_dimension: int = 768
    save_results: bool = True
    save_depth_map: bool = True
    results_dir: Path = Path("./results")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def depth_model_status(self) -> str:
        if not self.enable_depth_estimation:
            return "disabled"
        if self.depth_mock:
            return "mock"
        return "ready" if self.depth_model_path.exists() else "error"

    @property
    def lm_studio_openai_base_url(self) -> str:
        return self.lm_studio_url.rstrip("/") + "/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
