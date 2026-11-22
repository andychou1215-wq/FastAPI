# AI Inference Service Prototype

A FastAPI backend prototype that demonstrates request validation, concurrency control, system monitoring, and automated API testing for an AI inference service.

The service currently returns **mock LLM responses**. It does not load a machine-learning model or require a GPU, API key, or external AI provider.

## Features

- REST endpoints for service availability, system health, and mock text generation.
- Pydantic request validation: prompts must contain 1–1,000 characters and cannot be whitespace-only. Leading and trailing whitespace is removed.
- Up to two active generation requests per application process, enforced by a bounded semaphore.
- A one-second wait for an available generation slot; requests that cannot acquire a slot receive HTTP `503`.
- CPU, memory, and root-filesystem disk usage monitoring with `psutil`.
- Structured monitoring errors and logged inference failures.
- Six automated API tests and a separate five-request concurrency demonstration.

## Technology Stack

Python · FastAPI · Pydantic v2 · Uvicorn · psutil · pytest · HTTPX · Requests

## Getting Started

Use Python 3.10 or newer and a virtual environment. Dependency versions are not currently pinned in this repository.

### 1. Clone the repository

```bash
git clone https://github.com/andychou1215-wq/FastAPI.git
cd FastAPI
python -m venv .venv
```

### 2. Activate the environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install fastapi "pydantic>=2,<3" uvicorn psutil pytest httpx requests
```

### 4. Start the development server

```bash
python -m uvicorn main:app --reload
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Return the API availability message. |
| GET | `/health` | Return a static service-health response. |
| GET | `/system-health` | Report CPU, memory, disk usage, and monitoring errors. |
| POST | `/generate` | Validate a prompt and return a mock response. |

### Generate a mock response

Send a JSON request to `/generate`:

```json
{
  "prompt": "Explain CUDA"
}
```

Example response (latency varies):

```json
{
  "status": "success",
  "prompt": "Explain CUDA",
  "response": "Mock LLM response to: Explain CUDA",
  "usage": {
    "input_tokens": 2,
    "output_tokens": 6,
    "total_tokens": 8
  },
  "latency_seconds": 0.5
}
```

Generation includes a simulated 0.5-second processing delay. The `usage` fields count whitespace-separated words, **not model tokenizer tokens**. Reported latency starts after a semaphore slot is acquired, so it excludes time spent waiting for a slot.

### Generation errors

| Status | Trigger |
| --- | --- |
| `422` | Missing, empty, whitespace-only, oversized, or otherwise invalid prompt. |
| `503` | No generation slot becomes available within one second. |
| `500` | Inference processing fails. |

The reserved prompt `simulate_error` deliberately triggers an inference failure for testing. Clients receive `{"detail": "Internal inference error"}`; exception details are logged on the server. The semaphore is released in a `finally` block after processing, including when inference fails.

### System health

`/system-health` returns `cpu_percent`, `memory_percent`, `disk_percent`, `status`, and an `errors` object. Usage values are percentages.

| Status | Condition |
| --- | --- |
| `critical` | CPU ≥ 90%, memory ≥ 95%, or disk ≥ 95%. |
| `warning` | No critical threshold is reached, and CPU ≥ 70%, memory ≥ 80%, or disk ≥ 80%. |
| `healthy` | All measurements succeed and remain below warning thresholds. |
| `degraded` | At least one monitored metric raises a handled monitoring error. |

Unavailable measurements remain `null`, and the corresponding error is included in `errors`. A degraded status takes precedence over threshold classification. This endpoint returns its status in the JSON body; it does not map warning or critical readings to an HTTP error status.

`/health` is a simple availability endpoint; it does not check resource usage or model readiness.

## Testing

### Automated API tests

```bash
python -m pytest test_main.py -v
```

These tests use FastAPI's `TestClient`, so a separately running server is not required. They cover:

- Health endpoint response.
- Successful generation and usage accounting.
- Missing prompt rejection.
- Whitespace-only prompt rejection.
- Simulated inference failure.
- Successful generation after a failure.

Use the explicit filename above: `test_concurrency.py` sends live HTTP requests at module scope, so an unqualified `pytest` command can execute it during collection.

### Concurrent request demonstration

First start the server in one terminal:

```bash
python -m uvicorn main:app
```

Then run this command in another terminal with the virtual environment activated:

```bash
python test_concurrency.py
```

The script submits five requests using a thread pool and prints each request's ID, HTTP status, and elapsed time. It is an observational demonstration rather than an assertion-based benchmark. Status codes and timings depend on scheduling; five simultaneous submissions do not guarantee a `503` response.

## Source Files

| File | Responsibility |
| --- | --- |
| `main.py` | FastAPI application, request schema, monitoring, and generation handling. |
| `test_main.py` | Six API tests using `TestClient`. |
| `test_concurrency.py` | Live-server concurrency demonstration using Requests. |

## Scope and Limitations

This project is a learning and portfolio prototype. It currently has no real model integration, authentication, persistent storage, streaming generation, or distributed request limiter.

The concurrency limit is process-local. Running multiple Uvicorn workers creates a separate semaphore in each worker, rather than a shared service-wide limit. The generation handler uses synchronous processing and a simulated delay.

Potential next steps include integrating a model backend, pinning dependencies, expanding monitoring and saturation tests, and adding authentication and deployment configuration.

## Author

Yu-Siang Chou — Computer Science graduate student at Oregon State University.
