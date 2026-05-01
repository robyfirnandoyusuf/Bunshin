import threading
import time
import urllib.request
import urllib.error
import ssl
import json
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

SSL_CONTEXT = ssl._create_unverified_context()

@dataclass
class RaceResponse:
    thread_id: int
    status_code: int
    body: str
    duration: float
    error: str = ""

@dataclass
class RaceResult:
    test_name: str
    responses: list = field(default_factory=list)
    duration_total: float = 0.0

    def summary(self):
        print(f"\n=== {self.test_name} ===")
        print(f"Total duration : {self.duration_total:.3f}s")
        print(f"Total requests : {len(self.responses)}")

        from collections import Counter
        status_counts = Counter(
            r.status_code if not r.error else f"ERR:{r.error[:30]}"
            for r in self.responses
        )
        print("Status codes:")
        for status, count in status_counts.items():
            print(f"  {status} => {count}x")

        unique_bodies = set(r.body[:200] for r in self.responses if not r.error)
        print(f"Unique responses: {len(unique_bodies)}")
        if len(unique_bodies) > 1:
            print(" possible race condition!")
        else:
            print("  All responses are consistent")

    def suspicious_responses(self):
        """Return suspec response"""
        from collections import Counter
        bodies = [r.body[:200] for r in self.responses if not r.error]
        if not bodies:
            return []
        most_common = Counter(bodies).most_common(1)[0][0]
        return [r for r in self.responses if r.body[:200] != most_common]


class Bunshin:
    def __init__(self, workers: int = 20, timeout: int = 10):
        self.workers = workers
        self.timeout = timeout

    def _send_request(self, thread_id: int, url: str, method: str,
                      headers: dict, body: bytes | None) -> RaceResponse:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=SSL_CONTEXT) as resp:
                duration = time.perf_counter() - start
                return RaceResponse(
                    thread_id=thread_id,
                    status_code=resp.getcode(),
                    body=resp.read(4096).decode("utf-8", errors="ignore"),
                    duration=duration,
                )
        except urllib.error.HTTPError as e:
            duration = time.perf_counter() - start
            return RaceResponse(
                thread_id=thread_id,
                status_code=e.code,
                body=e.read(4096).decode("utf-8", errors="ignore"),
                duration=duration,
            )
        except Exception as e:
            return RaceResponse(
                thread_id=thread_id,
                status_code=0,
                body="",
                duration=time.perf_counter() - start,
                error=str(e),
            )

    def race(
        self,
        url: str,
        method: str = "POST",
        headers: dict = None,
        body: dict | str | bytes | None = None,
        count: int = 20,
        test_name: str = "race_test",
    ) -> RaceResult:
        if headers is None:
            headers = {}

        raw_body = None
        if isinstance(body, dict):
            raw_body = json.dumps(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif isinstance(body, str):
            raw_body = body.encode("utf-8")
        elif isinstance(body, bytes):
            raw_body = body

        result = RaceResult(test_name=test_name)
        barrier = threading.Barrier(count) 
        lock = threading.Lock()

        def worker(thread_id):
            barrier.wait()  # tunggu semua thread siap
            resp = self._send_request(thread_id, url, method, headers, raw_body)
            with lock:
                result.responses.append(resp)

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(worker, i) for i in range(count)]
            for f in futures:
                f.result()

        result.duration_total = time.perf_counter() - start
        return result
