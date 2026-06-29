import asyncio
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

THERMAL_ZONE_PATH = os.getenv("THERMAL_ZONE_PATH", "/sys/class/thermal/thermal_zone1/temp")
ESP32_URL = os.getenv("ESP32_URL", "http://192.168.3.114/status")
THERMAL_URL = os.getenv("THERMAL_URL", "/temp")
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


app = FastAPI(
    lifespan=lifespan,
    title="Thermal API",
    description=(
        "CPU temperature monitoring API for ZimaOS (Intel N100). "
        "Reads `/sys/class/thermal` via a sliding window and classifies the thermal trend. "
        "Designed to be polled by an ESP32 that controls a PWM cooler.\n\n"
        "**Trend directions:** `subida_brusca` (rate ≥ SPIKE_THRESHOLD), "
        "`subida_lenta` (rate ≥ RISE_THRESHOLD), `estavel`, `queda` (rate ≤ DROP_THRESHOLD)."
    ),
    version="1.1.0",
)

_mock_state: dict = {"temp_celsius": 45.0, "rate_of_change": 0.0}


class MockTempUpdate(BaseModel):
    temp_celsius: float = Field(
        default=45.0,
        description="Simulated CPU temperature in °C.",
        examples=[45.0, 72.5, 90.0],
    )
    rate_of_change: float = Field(
        default=0.0,
        description=(
            "Simulated rate of temperature change in °C/s. "
            "Controls the direction classification: "
            "≥ SPIKE_THRESHOLD → subida_brusca, "
            "≥ RISE_THRESHOLD → subida_lenta, "
            "≤ DROP_THRESHOLD → queda, "
            "otherwise → estavel."
        ),
        examples=[0.0, 0.5, 1.5, -0.5],
    )


def _classify(rate: float) -> str:
    if rate >= SPIKE_THRESHOLD:
        return "subida_brusca"
    elif rate >= RISE_THRESHOLD:
        return "subida_lenta"
    elif rate <= DROP_THRESHOLD:
        return "queda"
    return "estavel"


@app.get("/health", summary="Health check", tags=["Infra"])
def health():
    """Always returns 200. Used by the Docker healthcheck."""
    return {"status": "ok"}


@app.get("/temp", summary="Current temperature + trend", tags=["Thermal"])
def temp():
    """
    Returns the current CPU temperature and the thermal trend computed over the
    sliding window (`WINDOW_SIZE` samples, polled every `POLL_INTERVAL` seconds).

    - **warming_up**: returned while the window is filling up (first `WINDOW_SIZE` seconds).
    - **online**: window is full; includes `rate_of_change` (°C/s) and `direction`.
    """
    if len(window) < WINDOW_SIZE:
        return {"status": "warming_up", "samples": len(window), "required": WINDOW_SIZE}

    samples = list(window)
    first_temp, first_ts = samples[0]
    last_temp, last_ts = samples[-1]

    elapsed = last_ts - first_ts
    rate = (last_temp - first_temp) / elapsed if elapsed > 0 else 0.0
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
            "direction": _classify(rate),
        },
    }


@app.get("/temp-test", summary="Mock temperature + trend (for hardware testing)", tags=["Testing"])
def temp_test_get():
    """
    Returns the same JSON structure as `/temp` but using mock values set via `PUT /temp-test`.

    Use this endpoint to test the ESP32 hardware and PWM logic without needing to
    physically heat the CPU. Set any `rate_of_change` to trigger a specific `direction`
    and verify the cooler responds correctly.

    Defaults to `temp_celsius=45.0` and `rate_of_change=0.0` (direction: `estavel`)
    until overridden.
    """
    temp_c = _mock_state["temp_celsius"]
    rate = _mock_state["rate_of_change"]
    return {
        "status": "online",
        "current": {
            "temp_celsius": temp_c,
            "timestamp": round(time.time(), 3),
        },
        "window_stats": {
            "window_size_seconds": round(WINDOW_SIZE * POLL_INTERVAL, 2),
            "average_temp": temp_c,
        },
        "trend": {
            "rate_of_change": rate,
            "direction": _classify(rate),
        },
    }


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/config", summary="Frontend configuration defaults", tags=["Infra"])
def config():
    """Returns the URLs the frontend should poll by default."""
    return {"thermal_url": THERMAL_URL, "esp32_url": "/esp32/status"}


@app.get("/esp32/status", summary="ESP32 status proxy", tags=["Infra"])
async def esp32_proxy():
    """Proxies to the ESP32 at ESP32_URL env var to avoid browser CORS restrictions."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(ESP32_URL, timeout=5.0)
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="ESP32 timeout")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="ESP32 error")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.put("/temp-test", summary="Set mock temperature values", tags=["Testing"])
def temp_test_set(body: MockTempUpdate):
    """
    Updates the mock state used by `GET /temp-test`.

    Send any combination of `temp_celsius` and `rate_of_change` to simulate a specific
    thermal scenario. The `direction` field in the response will be classified using the
    same thresholds as the real `/temp` endpoint.

    Example — simulate a spike to trigger `subida_brusca`:
    ```json
    { "temp_celsius": 85.0, "rate_of_change": 1.5 }
    ```
    """
    _mock_state["temp_celsius"] = body.temp_celsius
    _mock_state["rate_of_change"] = body.rate_of_change
    return {"status": "ok", "temp_celsius": body.temp_celsius, "rate_of_change": body.rate_of_change}
