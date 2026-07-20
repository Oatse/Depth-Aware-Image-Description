from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Depth-Aware Image Description"
    app_env: str = "development"
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    tls_certfile: Path = Field(default=Path("./certs/localhost.pem"), validation_alias="TLS_CERTFILE")
    tls_keyfile: Path = Field(default=Path("./certs/localhost-key.pem"), validation_alias="TLS_KEYFILE")

    lm_studio_url: str = "http://localhost:1234"
    lm_studio_model: str = "google/gemma-4-e4b"
    lm_studio_timeout: int = 240
    lm_studio_health_timeout: float = 2.0
    lm_studio_max_tokens: int = 900
    gemma_mock: bool = False

    enable_depth_estimation: bool = True
    depth_model_path: Path = Path("./model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf")
    depth_input_size: int = 518
    depth_mock: bool = False
    analysis_queue_capacity: int = Field(default=8, ge=1, le=64)
    analysis_retained_jobs: int = Field(default=100, ge=65, le=1000)

    max_image_size_mb: int = 5
    image_max_dimension: int = 768
    save_results: bool = True
    save_depth_map: bool = True
    results_dir: Path = Path("./results")
    sensor_serial_port: str = Field(default="", validation_alias="SENSOR_SERIAL_PORT")
    sensor_serial_baud: int = Field(default=115200, validation_alias="SENSOR_SERIAL_BAUD")
    sensor_match_window_ms: int = Field(default=250, ge=1, le=5000, validation_alias="SENSOR_MATCH_WINDOW_MS")
    sensor_max_clock_skew_ms: int = Field(default=5000, ge=0, le=60000, validation_alias="SENSOR_MAX_CLOCK_SKEW_MS")
    sensor_reconnect_interval_ms: int = Field(default=1000, ge=100, le=30000, validation_alias="SENSOR_RECONNECT_INTERVAL_MS")
    sensor_status_window_ms: int = Field(default=1000, ge=100, le=10000, validation_alias="SENSOR_STATUS_WINDOW_MS")
    sensor_freshness_max_age_ms: int = Field(default=1000, ge=1, le=60000, validation_alias="SENSOR_FRESHNESS_MAX_AGE_MS")
    sensor_pair_disagreement_cm: float = Field(default=15.0, ge=0, le=500, validation_alias="SENSOR_PAIR_DISAGREEMENT_CM")
    sensor_clock_rtt_max_ms: int = Field(default=1000, ge=1, le=60000, validation_alias="SENSOR_CLOCK_RTT_MAX_MS")
    sensor_iot_strict: bool = Field(default=True, validation_alias="SENSOR_IOT_STRICT")
    sensor_calibration_path: Path = Field(default=Path("./config/sensor_camera_calibration.json"), validation_alias="SENSOR_CALIBRATION_PATH")

    experiment_artifact_profile: str = "final_44_gemma_e2b_20260708"
    experiment_images_dir: Path = Path("./dataset/final_images")
    experiment_annotations_path: Path = Path("./dataset/final_annotations.csv")
    experiment_predictions_path: Path = Path("./results/final_predictions_active_20260714.csv")
    experiment_evaluation_path: Path = Path("./results/final_evaluation_metrics_20260714.csv")

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
