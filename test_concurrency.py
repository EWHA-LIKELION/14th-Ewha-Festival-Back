import requests
import threading

URL = "http://127.0.0.1:8000/booths/1/"
VERSION = "2026-03-02 02:00:09.29613+09"

results = []

def send_patch():
    response = requests.patch(
        URL,
        json={"name": "updated"},
        headers={"X-Resource-Version": VERSION}
    )
    results.append(response.status_code)

threads = []

for _ in range(10):
    t = threading.Thread(target=send_patch)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("RESULTS:", results)
print("200 count:", results.count(200))
print("409 count:", results.count(409))