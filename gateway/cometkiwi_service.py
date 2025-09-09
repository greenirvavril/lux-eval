from flask import Flask, request, jsonify
from comet import download_model, load_from_checkpoint
import os
import sys
from waitress import serve

# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5005

model_path = download_model("Unbabel/wmt22-cometkiwi-da")
model = load_from_checkpoint(model_path)

@app.route("/")
def health():
    return "COMETKIWI22 service is running", 200

@app.route('/cometkiwi22', methods=['POST'])
def cometkiwi22():
    data = request.json
    sources = data.get('sources', [])
    candidates = data.get('candidates', [])

    if not sources or not candidates or len(sources) != len(candidates):
        return jsonify({'error': 'Invalid input: sources and candidates must be non-empty and of equal length'}), 400

    formatted_data = [{"src": s, "mt": c} for s, c in zip(sources, candidates)]
    model_output = model.predict(formatted_data, batch_size=8)
    output_dict = vars(model_output)
    scores = [s*100 for s in output_dict['scores']]
    system_score = output_dict['system_score']*100

    return jsonify({'cometkiwi22_scores': scores, 'system_score': system_score})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)
