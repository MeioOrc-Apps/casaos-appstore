import asyncio
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI

THERMAL_ZONE_PATH = os.getenv("THERMAL_ZONE_PATH", "/sys/class/thermal/thermal_zone1/temp")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "10"))
SPIKE_THRESHOLD = float(os.getenv("SPIKE_THRESHOLD", "1.0"))
RISE_THRESHOLD = float(os.getenv("RISE_THRESHOLD", "0.2"))
DROP_THRESHOLD = float(os.getenv("DROP_THRESHOLD", "-0.2"))

window: deque = deque(maxlen=WINDOW_SIZE)

os.makedirs("/app/logs", exist_ok=True)
_temp_logger = logging.getLogger("temps")
_temp_logger.setLevel(logging.INFO)
_temp_logger.propagate = False
_handler = TimedRotatingFileHandler(
    filename="/app/logs/temps.log",
    when="midnight",
    backupCount=30,
)
_handler.setFormatter(logging.Formatter("%(message)s"))
_temp_logger.addHandler(_handler)


async def _poll():
    while True:
        try:
            with open(THERMAL_ZONE_PATH) as f:
                temp = int(f.read().strip()) / 1000.0
            ts = time.monotonic()
            window.append((temp, ts))
            _temp_logger.info(f"{time.time():.3f},{temp:.3f}")
        except Exception as exc:
            logging.error("thermal read failed: %s", exc)
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_poll())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan, title="Thermal API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/temp")
def temp():
    if len(window) < WINDOW_SIZE:
        return {"status": "warming_up", "samples": len(window), "required": WINDOW_SIZE}

    samples = list(window)
    first_temp, first_ts = samples[0]
    last_temp, last_ts = samples[-1]

    elapsed = last_ts - first_ts
    rate = (last_temp - first_temp) / elapsed if elapsed > 0 else 0.0

    if rate >= SPIKE_THRESHOLD:
        direction = "subida_brusca"
    elif rate >= RISE_THRESHOLD:
        direction = "subida_lenta"
    elif rate <= DROP_THRESHOLD:
        direction = "queda"
    else:
        direction = "estavel"

    avg = sum(t for t, _ in samples) / len(samples)

    return {
        "status": "online",
        "current": {
            "temp_celsius": round(last_temp, 3),
            "timestamp": round(time.time(), 3),
        },
        "window_stats": {
            "window_size_seconds": round(elapsed, 2),
            "average_temp": round(avg, 3),
        },
        "trend": {
            "rate_of_change": round(rate, 3),
            "direction": direction,
        },
    }
