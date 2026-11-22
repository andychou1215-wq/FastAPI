from concurrent.futures import ThreadPoolExecutor
import time

import requests

API_URL = "http://127.0.0.1:8000/generate"

def send_request(request_id):
    start = time.perf_counter()
    response = requests.post(
        API_URL,
        json={
            "prompt": f"Request number {request_id}"
        },
        timeout=5
    )

    elapsed = time.perf_counter() - start

    return {
        "request_id": request_id,
        "status_code": response.status_code,
        "elapsed": round(elapsed, 3)
    }


with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(
        executor.map(send_request, range(1, 6))
    )

for result in results:
    print(result)