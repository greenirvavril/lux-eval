from bleurt_pytorch import BleurtConfig, BleurtForSequenceClassification, BleurtTokenizer
from flask import Flask, request, jsonify
import os
import sys
import torch
from waitress import serve


# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

config = BleurtConfig.from_pretrained('lucadiliello/BLEURT-20')
model = BleurtForSequenceClassification.from_pretrained('lucadiliello/BLEURT-20')
tokenizer = BleurtTokenizer.from_pretrained('lucadiliello/BLEURT-20')

@app.route("/")
def health():
    return "BLEURT service is running", 200

@app.route('/bleurt20', methods=['POST'])
def bleurtscore():
    data = request.json
    references = data.get('references', [])
    candidates = data.get('candidates', [])

    if not references or not candidates or len(references) != len(candidates):
        return jsonify({'error': 'Invalid input: references and candidates must be non-empty and of equal length'}), 400

    model.eval()
    with torch.no_grad():
        inputs = tokenizer(references, candidates, padding='longest', return_tensors='pt')
        res = model(**inputs).logits.flatten().tolist()

    for i in range(len(res)):
        res[i] = res[i] * 100
    return jsonify({'bleurt_scores': res})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)

