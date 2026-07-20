from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.routes.analyze import router as analyze_router
from app.routes.analyze_jobs import router as analyze_jobs_router
from app.routes.analyze_jobs import run_analysis_job
from app.routes.experiment_status import router as experiment_status_router
from app.routes.sensor_status import router as sensor_status_router
from app.schemas import HealthResponse
from models.gemma_client import GemmaClient
from services.analysis_jobs import AnalysisJobService
from services.sensor_bridge import SensorBridge


settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    analysis_jobs = AnalysisJobService(
        runner=run_analysis_job,
        queue_capacity=settings.analysis_queue_capacity,
        retained_jobs=settings.analysis_retained_jobs,
    )
    application.state.analysis_jobs = analysis_jobs
    sensor_bridge = SensorBridge(
        settings.sensor_serial_port,
        settings.sensor_serial_baud,
        reconnect_interval_seconds=settings.sensor_reconnect_interval_ms / 1000,
    )
    sensor_bridge.start()
    application.state.sensor_bridge = sensor_bridge
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(analysis_jobs.serve)
        yield
        sensor_bridge.stop()
        await analysis_jobs.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Prototype implementasi depth-aware image description untuk citra indoor.",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory=str(settings.results_dir)), name="results")
templates = Jinja2Templates(directory="templates")
app.include_router(analyze_router)
app.include_router(analyze_jobs_router)
app.include_router(experiment_status_router)
app.include_router(sensor_status_router)
gemma_client = GemmaClient(settings)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        success=True,
        app=settings.app_name,
        backend="ok",
        gemma=await gemma_client.check_status(),
        depth_model=settings.depth_model_status,
    )
