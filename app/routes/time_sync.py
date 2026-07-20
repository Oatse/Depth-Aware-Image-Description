import time

from fastapi import APIRouter

router = APIRouter()


@router.get("/time-sync")
async def time_sync() -> dict[str, int | str]:
    return {"server_time_ms": int(time.time() * 1000), "clock_domain": "unix_epoch_ms"}
