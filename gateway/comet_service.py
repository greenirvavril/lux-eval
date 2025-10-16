from comet import download_model, load_from_checkpoint
import os
from flask import Flask, request, jsonify
import os
import sys
from waitress import serve

# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5008

@app.route("/")
def health():
    return "COMET service is running", 200


model_path = download_model("Unbabel/XCOMET-XL")
model = load_from_checkpoint(model_path)

@app.route('/xcometxl', methods=['POST'])
def cometscore():
    data = request.json
    references = data.get('references', [])
    candidates = data.get('candidates', [])

    if not references or not candidates or len(references) != len(candidates):
        return jsonify({'error': 'Invalid input: references and candidates must be non-empty and of equal length'}), 400

    # Prepare data in the format expected by XCOMET
    eval_data = [
        {"mt": mt, "ref": ref}
        for mt, ref in zip(candidates, references)
    ]

    # Load and run the model
    model_output = model.predict(eval_data, batch_size=8, gpus=1) # may have to adjust number of gpus depending on your system

    # Extract scores
    # model_output is typically a list of dicts like [{'score': 0.8732}, ...]
    res = model_output.scores
    for i in range(len(res)):
        res[i] = res[i] * 100
    return jsonify({'xcometxl_scores': res})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)

