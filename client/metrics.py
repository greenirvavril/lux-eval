import numpy as np
import requests
from tqdm import tqdm
from yaspin import yaspin
import threading
import time

def output_format(segment_scores: list):
    """Convert segment scores to dict with system score."""
    system_score = np.mean(segment_scores) if segment_scores else 0.0
    return {"segment_scores": segment_scores, "system_score": system_score}

def read_file_lines(path: str, strip=True):
    """Read a file and return a list of lines."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if strip:
        lines = [line.strip() for line in lines if line.strip()]
    return lines

def validate_lines(lines1, lines2, name1="Reference", name2="Candidate"):
    """Ensure files are not empty and have the same number of lines."""
    if not lines1 or not lines2:
        raise ValueError(f"{name1} or {name2} file is empty.")
    if len(lines1) != len(lines2):
        raise ValueError(f"{name1} and {name2} must have the same number of lines. Got {len(lines1)} vs {len(lines2)}")

# Metric configuration
metric_config = {
    "bertscore": {"files": ["reference", "candidate"], "payload_keys": {"references": "reference", "candidates": "candidate"}, "score_key": "bert_scores", "language": True},
    "bleurt20": {"files": ["reference", "candidate"], "payload_keys": {"references": "reference", "candidates": "candidate"}, "score_key": "bleurt_scores", "language": False},
    "xcometxl": {"files": ["reference", "candidate"], "payload_keys": {"references": "reference", "candidates": "candidate"}, "score_key": "xcometxl_scores", "language": False},
    "luxembedder": {"files": ["source", "candidate"], "payload_keys": {"sources": "source", "candidates": "candidate"}, "score_key": "luxembedder_scores", "language": False},
    "sacrebleu": {"files": ["reference", "candidate"], "payload_keys": {"references": "reference", "candidates": "candidate"}, "score_key": None, "language": False}
}

def score_metric(url, model, files: dict, metric_name: str, language="en"):
    """
    Generic scoring function with tqdm for prep and spinner for API wait.
    """
    cfg = metric_config[metric_name]
    try:
        # Read required files
        file_lines = {}
        for f in cfg["files"]:
            if f in files and files[f]:
                file_lines[f] = read_file_lines(files[f])

        # Validate line counts
        if "reference" in file_lines and "candidate" in file_lines:
            validate_lines(file_lines["reference"], file_lines["candidate"])
        if "source" in file_lines and "candidate" in file_lines:
            validate_lines(file_lines["source"], file_lines["candidate"], "Source", "Candidate")

        # Build payload
        data = {}
        for key, file_key in cfg["payload_keys"].items():
            data[key] = file_lines[file_key]
        if cfg.get("language"):
            data["language"] = language.lower()

        total_segments = len(next(iter(file_lines.values())))  # number of lines
        response_container = {}

        def do_request():
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=data, headers=headers)
                response_container["response"] = response
            except Exception as e:
                response_container["error"] = str(e)

        # Step 1: prep with tqdm
        with tqdm(total=total_segments, desc=f"{model} - {metric_name} (prep)", unit="lines") as pbar:
            for _ in range(total_segments):
                time.sleep(0.001)  # simulate per-line prep
                pbar.update(1)

        # Step 2: API request with spinner
        thread = threading.Thread(target=do_request)
        thread.start()
        with yaspin(text=f"{model} - {metric_name} (waiting on API)", color="cyan") as spinner:
            while thread.is_alive():
                time.sleep(0.1)
            thread.join()
            if "error" in response_container:
                spinner.fail(":(")
                raise RuntimeError(response_container["error"])
            else:
                spinner.ok(":)")

        response = response_container["response"]
        if response.status_code != 200:
            print(f"Error: {model}, {metric_name}, {response.status_code} - {response.text}")
            return {"error": f"API request failed with status code {response.status_code}"}

        # Handle standard metrics
        if cfg["score_key"]:
            segment_scores = response.json().get(cfg["score_key"], []) or []
            return output_format(segment_scores)

        # Special handling for sacrebleu
        if metric_name == "sacrebleu":
            data = response.json()
            return {"bleu": data.get("bleu_score", data.get("BLEU")),
                    "chrF2": data.get("chrF2"),
                    "TER": data.get("TER")}

        return response.json()

    except Exception as e:
        print(f"{model}: {metric_name} scoring failed: {e}")
        return {"error": str(e)}
