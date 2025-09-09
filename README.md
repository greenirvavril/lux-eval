# Lux-Eval

## Installation

```bash
# Clone the Lux-Eval repository
git clone https://github.com/greenirvavril/lux-eval.git

# Navigate into the project directory
cd lux-eval

# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
````

---

## Getting Started

The client requires the **gateway's IP address** to connect. Follow these steps to get started.

### 1. Launch the Gateway

```bash
cd gateway
source main_venv/bin/activate
python main_gateway.py
```

Let it run until the output shows:

```
Gateway is running!
  - Local access (same machine): http://127.0.0.1:5000
  - Network access (other machines should use this IP): http://192.168.X.X:5000
```

* Use the **local access URL** if the gateway is running on the same machine as the client.
* Use the **network access URL** if the gateway is running on another machine on the same network.

---

### 2. Configure the Client

1. Copy the appropriate IP address from the gateway output.
2. Navigate to the client folder:

```bash
cd client
```

3. Open `client.py` and locate:

```python
URL = ""  # <-- enter your gateway IP, e.g.: "http://192.168.X.X:5000"
```

4. Paste the IP address and configure the metrics you want to use (`True` or `False`).
5. Save the file.

---

### 3. Launch the Client

In a new terminal:

```bash
cd client  # adjust path if necessary
source client_venv/bin/activate
python client.py
```

The client will connect to the gateway and start evaluating metrics as configured.

---

### Notes

* Ensure that **port 5000** is open on the gateway machine if running on a network.
* The gateway must be running before starting the client.
* For testing on the same machine, you can always use `http://127.0.0.1:5000`.

```
