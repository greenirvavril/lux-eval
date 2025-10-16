from bleurt import score
from flask import Flask, request, jsonify
import os
import sys
from waitress import serve

# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

@app.route("/")
def health():
    return "BLEURT service is running", 200


checkpoint = "/home/nils/nilseval/bleurt-20-new/bleurt/BLEURT-20"
scorer = score.BleurtScorer(checkpoint)

@app.route('/bleurt20', methods=['POST'])
def bleurtscore():
    data = request.json
    references = data.get('references', [])
    candidates = data.get('candidates', [])

    if not references or not candidates or len(references) != len(candidates):
        return jsonify({'error': 'Invalid input: references and candidates must be non-empty and of equal length'}), 400

    res = scorer.score(references=references, candidates=candidates)
    for i in range(len(res)):
        res[i] = max(0, min(res[i] * 100, 100))
    return jsonify({'bleurt_scores': res})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)

