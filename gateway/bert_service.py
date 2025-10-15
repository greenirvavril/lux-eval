from bert_score import BERTScorer
from flask import Flask, request, jsonify
import os
from sacrebleu.metrics import BLEU, CHRF, TER
import sys
from waitress import serve

# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5002

@app.route("/")
def health():
    return "BERTSCORE and BLEU service are running", 200


@app.route('/bertscore', methods=['POST'])
def bertscore():
    data = request.json
    references = data.get('references', [])
    candidates = data.get('candidates', [])
    language = data.get("language", "").lower()

    if not references or not candidates or len(references) != len(candidates):
        return jsonify({'error': 'Invalid input'}), 400

    if language in ["en", "english", "eng"]:
        model_path = "/home/nils/nilseval/models/models--microsoft--deberta-xlarge-mnli/snapshots/5b07a9086c1dbb79981ff7b05b4d1ad83b3af51c"
        num_layers = 40
    else:
        model_path = "/home/nils/nilseval/models/models--FacebookAI--xlm-roberta-large/snapshots/c23d21b0620b635a76227c604d44e43a9f0ee389"
        num_layers = 17

    scorer = BERTScorer(model_type=model_path, num_layers=num_layers, lang=language, rescale_with_baseline=False)
    P, R, F1 = scorer.score(candidates, references) # precision, recall, harmonic mean
    F1 = F1 * 100
    return jsonify({"bert_scores": F1.tolist()})

@app.route('/sacrebleu', methods=['POST'])
def sacrebleu():
    data = request.json
    references = [data.get('references', [])]
    candidates = data.get('candidates', [])

    bleu = BLEU()
    bleu_scores = bleu.corpus_score(candidates, references)

    chrf = CHRF()
    chrF2 = chrf.corpus_score(candidates, references)

    ter = TER()
    ter_scores = ter.corpus_score(candidates, references)

    return jsonify({'bleu_score': bleu_scores.score, "chrF2": chrF2.score, "TER": ter_scores.score})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)


