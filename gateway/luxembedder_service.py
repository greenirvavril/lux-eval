from flask import Flask, request, jsonify
import sys
from waitress import serve
from sentence_transformers import SentenceTransformer

# Run on GPU 0
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5006

def normalise_score(x: float) -> float:
    """
    Normalize a score from [0, 100] into [0, 1],
    mapping [0, 70) -> 0 and [70, 100] linearly to [0, 1].

    Args:
        x (float): Input score between 0 and 100.

    Returns:
        float: Normalized score in [0, 1].
    """
    x = max(0.0, min(100.0, x))  # clamp to [0,100]
    if x < 80:
        return 0.0
    elif x > 100:
        raise ValueError("Input must be between 0 and 100.")
    else:
        res = (x - 80) / (100 - 80)
        return res * 100

@app.route("/")
def health():
    return "Luxembedder service is running", 200

# Load the model
model = SentenceTransformer('fredxlpy/LuxEmbedder')

@app.route('/luxembedder', methods=['POST'])
def luxembedderscore():
    data = request.json
    sources = data.get('sources', [])
    candidates = data.get('candidates', [])

    if not sources or not candidates or len(sources) != len(candidates):
        return jsonify({'error': 'Invalid input: sources and candidates must be non-empty and of equal length'}), 400

    # Encode sentences
    source_embeddings = model.encode(sources, convert_to_tensor=True)
    candidate_embeddings = model.encode(candidates, convert_to_tensor=True)

    # Compute cosine similarity scores (element-wise multiplication and summation over dimension)
    res = (source_embeddings * candidate_embeddings).sum(dim=1).cpu().numpy()
    res = (res * 100).tolist()  # scale and convert to list
    for idx in range(len(res)):
        res[idx] = normalise_score(res[idx])


    return jsonify({'luxembedder_scores': res})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=port)

