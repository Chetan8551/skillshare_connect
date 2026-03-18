#mock_interview\evaluator.py
from sentence_transformers import SentenceTransformer, util

SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
_device = "cpu"

def get_sbert():
    global _model
    if _model is None:
        _model = SentenceTransformer(SBERT_MODEL_NAME, device=_device)
    return _model

def semantic_similarity(a: str, b: str):
    model = get_sbert()
    embs = model.encode([a, b], convert_to_tensor=True)
    sim = util.pytorch_cos_sim(embs[0], embs[1])
    return float(sim.item())
