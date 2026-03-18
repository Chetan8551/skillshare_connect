#mock_interview\llm_utils.py
from sentence_transformers import SentenceTransformer, util

SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_sbert = SentenceTransformer(SBERT_MODEL_NAME)

def semantic_similarity(a, b):
    embs = _sbert.encode([a, b], convert_to_tensor=True)
    sim = util.pytorch_cos_sim(embs[0], embs[1])
    return float(sim.item())
