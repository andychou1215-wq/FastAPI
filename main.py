from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
import psutil
import os
import logging
import time
import threading

logger = logging.getLogger(__name__)
app = FastAPI()

MAX_CONCURRENT_REQUESTS = 2
inference_semaphore = threading.BoundedSemaphore(
    value=MAX_CONCURRENT_REQUESTS
)

class GenerateRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=1000
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "Prompt cannot be empty"
            )
        return value

@app.get("/")
def root():
    return {
        "message": "AI Server API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AI Server"
    }

def get_health_status(cpu, ram, disk):
    usages = [cpu, ram, disk]
    if any(usage >= 95 for usage in usages[1:]) or cpu >= 90:
        return "critical"
    if any(usage >= 80 for usage in usages[1:]) or cpu >= 70:
        return "warning"
    return "healthy"

@app.get("/system-health")
def system_health():
    result = {
        "status": "healthy",
        "cpu_percent": None,
        "memory_percent": None,
        "disk_percent": None,
        "errors": {}
    }

    try:
        result["cpu_percent"] = psutil.cpu_percent(
            interval=0.1
        )
    except (OSError, RuntimeError):
        logger.exception("CPU monitoring failed")
        result["errors"]["cpu"] = "CPU monitoring unavailable"

    try:
        result["memory_percent"] = (
            psutil.virtual_memory().percent
        )
    except (OSError, RuntimeError):
        logger.exception("RAM monitoring failed")
        result["errors"]["memory"] = "RAM monitoring unavailable"

    try:
        disk_path = os.path.abspath(os.sep)
        result["disk_percent"] = (
            psutil.disk_usage(disk_path).percent
        )
    except (OSError, RuntimeError):
        logger.exception("Disk monitoring failed")
        result["errors"]["disk"] = "Disk monitoring unavailable"

    if result["errors"]:
        result["status"] = "degraded"
    else:
        result["status"] = get_health_status(
            result["cpu_percent"],
            result["memory_percent"],
            result["disk_percent"]
        )

    return result

@app.post("/generate")
def generate(request: GenerateRequest):

    acquired = inference_semaphore.acquire(
        timeout=1.0
    )

    if not acquired:
        raise HTTPException(
            status_code=503,
            detail="Inference server is busy"
        )

    try:
        start_time = time.perf_counter()

        # Simulate inference failure for testing
        if request.prompt == "simulate_error":
            raise RuntimeError(
                "Simulated inference failure"
            )

        # Normal mock inference
        time.sleep(0.5)

        mock_response = (
            f"Mock LLM response to: {request.prompt}"
        )

        input_tokens = len(request.prompt.split())
        output_tokens = len(mock_response.split())

        latency = time.perf_counter() - start_time

        return {
            "status": "success",
            "prompt": request.prompt,
            "response": mock_response,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "latency_seconds": round(latency, 3)
        }

    except Exception:
        logger.exception("LLM inference failed")

        raise HTTPException(
            status_code=500,
            detail="Internal inference error"
        ) from None

    finally:
        inference_semaphore.release()