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

def wait_for_service(url, timeout=120):
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

def get_client_accessible_ip():
    """
    Get the IP address that clients can use to reach this machine.
    Works for local or network clients.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send data; just used to detect the outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# -------- Service definitions --------
SERVICES = {
    "bleurt": {
        "venv": "./bleurt_venv/bin/python",
        "script": "bleurt_service.py",
        "endpoints": ["/bleurt20"],
    },
    "bert": {
        "venv": "./bert_venv/bin/python",
        "script": "bert_service.py",
        "endpoints": ["/bertscore", "/sacrebleu"],
    },
    "luxembedder": {
        "venv": "./luxembedder_venv/bin/python",
        "script": "luxembedder_service.py",
        "endpoints": ["/luxembedder"],
    },
    "xcometxl": {
        "venv": "./comet_venv/bin/python",
        "script": "comet_service.py",
        "endpoints": ["/xcometxl"],
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
        client_ip = get_client_accessible_ip()
        print("Gateway is running!")
        print(f"  - Local access (same machine): http://127.0.0.1:5000")
        print(f"  - Network access (other machines should use this IP): http://{client_ip}:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        for proc in processes.values():
            proc.terminate()
