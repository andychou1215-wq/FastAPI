from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_generate_success():
    response = client.post(
        "/generate",
        json={"prompt": "Explain CUDA"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["prompt"] == "Explain CUDA"

    assert "usage" in data
    assert "latency_seconds" in data

    assert data["usage"]["total_tokens"] == (
        data["usage"]["input_tokens"]
        + data["usage"]["output_tokens"]
    )


def test_missing_prompt():
    response = client.post(
        "/generate",
        json={"message": "Hello"}
    )

    assert response.status_code == 422


def test_empty_prompt():
    response = client.post(
        "/generate",
        json={"prompt": "   "}
    )

    assert response.status_code == 422


def test_inference_failure():
    response = client.post(
        "/generate",
        json={"prompt": "simulate_error"}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Internal inference error"
    )


def test_recovery_after_failure():
    client.post(
        "/generate",
        json={"prompt": "simulate_error"}
    )

    response = client.post(
        "/generate",
        json={"prompt": "Hello again"}
    )

    assert response.status_code == 200