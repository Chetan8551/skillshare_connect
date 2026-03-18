from sentence_transformers import SentenceTransformer, util

# Load model once (this is cached locally after first run)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Example reference & student answer
reference = "Gaming improves problem-solving skills by requiring quick decisions and strategic planning."
student_answer = "Playing games like puzzles and shooters help me improve my focus and make faster decisions."

# Generate embeddings
ref_emb = model.encode(reference, convert_to_tensor=True)
ans_emb = model.encode(student_answer, convert_to_tensor=True)

# Compute similarity
similarity = util.cos_sim(ref_emb, ans_emb).item()

print(f"Similarity Score: {similarity:.2f}")
