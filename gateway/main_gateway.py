from flask import Flask, request, jsonify
import requests
import subprocess
import time
import socket

# -------- Helpers --------
def get_free_port():
    """Find a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def wait_for_service(url, timeout=60):
    """Wait until a service responds with 200 OK."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(url)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service at {url} did not start in {timeout}s")

# -------- Service definitions --------
SERVICES = {
    "bleurt": {
        "venv": "./bleurtvenv/bin/python",
        "script": "bleurt_service.py",
        "endpoints": ["/bleurt20"],
    },
    "bert": {
        "venv": "./bertvenv/bin/python",
        "script": "bert_service.py",
        "endpoints": ["/bertscore", "/sacrebleu"],  # both handled by the same backend
    },
    "cometkiwi22": {
        "venv": "./cometkiwivenv/bin/python",
        "script": "cometkiwi_service.py",
        "endpoints": ["/cometkiwi22"],
    },
    "luxembedder": {
        "venv": "./luxembeddervenv/bin/python",
        "script": "luxembedder_service.py",
        "endpoints": ["/luxembedder"],
    },
}

# -------- Launch services --------
processes = {}
ports = {}

for name, cfg in SERVICES.items():
    port = get_free_port()
    ports[name] = port
    print(f"Starting {name.upper()} service on port {port}")
    proc = subprocess.Popen([cfg["venv"], cfg["script"], str(port)])
    processes[name] = proc
    wait_for_service(f"http://localhost:{port}/")

# -------- Flask gateway --------
app = Flask(__name__)

@app.route('/')
def home():
    return "Gateway is running", 200

# Dynamically create proxy routes
def make_proxy(service_name, endpoint):
    def proxy():
        try:
            res = requests.post(
                f"http://localhost:{ports[service_name]}{endpoint}",
                json=request.get_json()
            )
            res.raise_for_status()
            return jsonify(res.json()), res.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return proxy

for service_name, cfg in SERVICES.items():
    for endpoint in cfg["endpoints"]:
        app.add_url_rule(endpoint, f"{service_name}_{endpoint}", make_proxy(service_name, endpoint), methods=["POST"])

# -------- Entry point --------
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        for proc in processes.values():
            proc.terminate()
