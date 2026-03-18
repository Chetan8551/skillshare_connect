import json
import re
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .ollama_client import call_ollama
from sentence_transformers import SentenceTransformer, util

# Load embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Session memory: track question, answer, feedback, score
user_sessions = {}  # session_id -> {"skill": str, "name": str, "history": [{"question","answer","feedback","score"}], "current_question": str}


def start_interview(request):
    return render(request, "mock_interview/mock_interview.html")


@csrf_exempt
def start_dynamic_interview(request):
    """Start a new interview session"""
    if request.method != "POST":
        return JsonResponse({"error": "POST with 'skill' required"})

    try:
        data = json.loads(request.body.decode("utf-8"))
        skill = data.get("skill", "Python").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON"})

    session_id = str(len(user_sessions) + 1)
    user_sessions[session_id] = {
        "skill": skill, 
        "name": None,
        "history": [],
        "current_question": None,
        "state": "get_name",  # States: get_name, interview, finished
        "question_count": 0
    }

    # First ask for name
    first_question = "Hello! Welcome to the interview. To get started, what is your name?"
    user_sessions[session_id]["current_question"] = first_question
    
    # Return the question - the frontend will handle speaking it
    return JsonResponse({"session_id": session_id, "question": first_question})


def evaluate_semantic_score(reference_text: str, user_answer: str) -> float:
    if not reference_text.strip():
        return 0.5
    ref_emb = embedding_model.encode(reference_text, convert_to_tensor=True)
    ans_emb = embedding_model.encode(user_answer, convert_to_tensor=True)
    similarity = util.cos_sim(ref_emb, ans_emb).item()
    return round(float(similarity), 2)


def is_interruption(user_answer, current_question):
    """Check if the user is asking for clarification rather than answering"""
    lower_answer = user_answer.lower()
    
    # Check for interruption phrases
    interruption_phrases = [
        "can you explain", "what do you mean", "i don't understand", 
        "i don't know", "can you clarify", "repeat that", "say that again",
        "what does that mean", "can you help me understand", "i'm not sure",
        "could you explain", "can you tell me more", "i need clarification"
    ]
    
    # Check if the user is asking for clarification rather than answering
    is_clarification = any(phrase in lower_answer for phrase in interruption_phrases)
    
    # Also check if the answer is very short (likely not a real answer)
    is_short = len(user_answer.split()) < 3
    
    return is_clarification or is_short


def handle_user_interruption(session, user_answer):
    """Handle user requests to repeat or clarify questions"""
    lower_answer = user_answer.lower()
    
    if any(phrase in lower_answer for phrase in ["repeat", "say again", "didn't hear", "can you repeat"]):
        return f"Sure, I'll repeat: {session['current_question']}"
    
    if any(phrase in lower_answer for phrase in ["don't understand", "explain", "clarify", "what do you mean", "can you explain", "what does that mean"]):
        clarification_prompt = f"""
        The candidate asked for clarification on this interview question: "{session['current_question']}"
        The question is about {session['skill']}.
        Provide a clear, helpful explanation of what this question means.
        Keep your response to 1-2 sentences maximum.
        Speak directly to the candidate {session.get('name', '')}.
        """
        clarification = call_ollama(clarification_prompt).strip()
        
        # Clean up the response to remove any meta-text
        if "candidate:" in clarification.lower() or "interviewer:" in clarification.lower():
            # Extract just the response part
            lines = clarification.split('\n')
            for line in lines:
                if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                    clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                    if clean_line.strip():
                        return clean_line.strip()
        
        return clarification if clarification else f"Let me rephrase: {session['current_question']}"
    
    # Handle other user questions
    if any(phrase in lower_answer for phrase in ["what is", "can you tell me", "how to", "why", "what about"]):
        question_prompt = f"""
        The candidate asked a question during the interview: "{user_answer}"
        The interview is about {session['skill']}.
        As the interviewer, provide a helpful but concise answer to their question.
        Keep your response to 1-2 sentences maximum.
        Speak directly to the candidate {session.get('name', '')}.
        """
        answer = call_ollama(question_prompt).strip()
        
        # Clean up the response to remove any meta-text
        if "candidate:" in answer.lower() or "interviewer:" in answer.lower():
            # Extract just the response part
            lines = answer.split('\n')
            for line in lines:
                if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                    clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                    if clean_line.strip():
                        return clean_line.strip()
        
        return answer if answer else "I'm not sure how to answer that. Let's continue with the interview."
    
    return None


@csrf_exempt
def answer_dynamic_question(request):
    """
    Receive user's answer, evaluate, generate concise feedback, then generate next question dynamically.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST with 'session_id' and 'answer' required"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        session_id = payload.get("session_id")
        user_answer = payload.get("answer", "").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if session_id not in user_sessions:
        return JsonResponse({"error": "Invalid session"}, status=400)

    session = user_sessions[session_id]
    skill = session["skill"]
    history = session["history"]
    current_question = session["current_question"]

    # Check if user is asking for a clarification/interruption rather than answering
    if is_interruption(user_answer, current_question):
        interruption_response = handle_user_interruption(session, user_answer)
        if interruption_response:
            # If it's a repeat request, keep the same question
            if any(phrase in user_answer.lower() for phrase in ["repeat", "say again", "didn't hear"]):
                return JsonResponse({
                    "feedback": None,
                    "score": None,
                    "next_question": interruption_response,
                    "final_feedback": None,
                    "repeat_question": True
                })
            # For explanations or answers to user questions, provide response but move to next question
            else:
                # Generate next question after answering user's query
                next_prompt = f"""
                You are a professional interviewer for {skill}.
                Candidate Name: {session.get('name', 'Candidate')}
                
                The candidate just asked: "{user_answer}"
                You provided this response: "{interruption_response}"
                
                Now continue the interview with a relevant follow-up question about {skill}.
                Ask only one question at a time. Keep it professional and concise.
                Speak directly to the candidate.
                """
                next_question = call_ollama(next_prompt).strip()
                
                # Clean up the response to remove any meta-text
                if "candidate:" in next_question.lower() or "interviewer:" in next_question.lower():
                    lines = next_question.split('\n')
                    for line in lines:
                        if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                            clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                            if clean_line.strip():
                                next_question = clean_line.strip()
                                break
                
                session["current_question"] = next_question
                
                return JsonResponse({
                    "feedback": interruption_response,
                    "score": None,
                    "next_question": next_question,
                    "final_feedback": None
                })

    # Handle name capture
    if session["state"] == "get_name":
        session["name"] = user_answer
        session["state"] = "interview"
        
        # Start the actual interview
        prompt = f"""
        You are a professional interviewer for {skill}. 
        {session['name']} is the candidate. Address them by name.
        Start with a concise professional question about {skill}.
        Make sure the question is appropriate for the skill level.
        Ask only one question at a time.
        Speak directly to the candidate.
        """
        first_tech_question = call_ollama(prompt).strip()
        
        # Clean up the response to remove any meta-text
        if "candidate:" in first_tech_question.lower() or "interviewer:" in first_tech_question.lower():
            lines = first_tech_question.split('\n')
            for line in lines:
                if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                    clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                    if clean_line.strip():
                        first_tech_question = clean_line.strip()
                        break
        
        session["current_question"] = first_tech_question
        session["question_count"] += 1
        
        return JsonResponse({
            "feedback": f"Nice to meet you, {user_answer}. Let's begin the interview.",
            "score": None,
            "next_question": first_tech_question,
            "final_feedback": None
        })

    # For technical questions, evaluate the answer
    reference_text = current_question if current_question else "Explain your experience with " + skill
    score = evaluate_semantic_score(reference_text, user_answer)

    # Concise feedback prompt
    feedback_prompt = f"""
    You are a professional interviewer. Provide a concise feedback for the following answer:
    Skill: {skill}
    Candidate Name: {session.get('name', 'Candidate')}
    Question: "{reference_text}"
    Candidate Answer: "{user_answer}"
    
    Provide feedback in exactly this format:
    "Good: [one positive aspect]. Improvement: [one specific suggestion]."
    
    Keep it to exactly 1 sentence for good and 1 sentence for improvement.
    Speak directly to the candidate.
    """
    feedback = call_ollama(feedback_prompt).strip()
    
    # Clean up the feedback to remove any meta-text
    if "candidate:" in feedback.lower() or "interviewer:" in feedback.lower():
        lines = feedback.split('\n')
        for line in lines:
            if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                if clean_line.strip():
                    feedback = clean_line.strip()
                    break
    
    if not feedback:
        # fallback feedback
        if score >= 0.8:
            feedback = "Good: Comprehensive answer. Improvement: Could add more specific examples."
        elif score >= 0.6:
            feedback = "Good: Clear response. Improvement: Try to elaborate with more details."
        else:
            feedback = "Good: Attempted to answer. Improvement: Please provide more specific information."

    # Add to history
    history.append({
        "question": reference_text,
        "answer": user_answer,
        "feedback": feedback,
        "score": score
    })

    # Check if we should end the interview (after 5-8 questions)
    if session["question_count"] >= 7:
        session["state"] = "finished"
        # Generate final feedback summary
        valid_scores = [item["score"] for item in history if item.get("score") is not None]
        total_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        summary_prompt = f"""
        You are a professional interviewer. Provide a concise final feedback summary for {session.get('name', 'the candidate')}
        based on the following interview performance about {skill}:
        {json.dumps(history, indent=2)}
        
        Overall Score: {total_score:.2f}/1.0
        
        Provide feedback in exactly this format:
        "Overall: [brief summary]. Strengths: [2 key strengths]. Areas to improve: [1 specific area]."
        
        Keep it to maximum 3 sentences total.
        Speak directly to the candidate.
        """
        final_feedback = call_ollama(summary_prompt).strip()
        
        # Clean up the final feedback to remove any meta-text
        if "candidate:" in final_feedback.lower() or "interviewer:" in final_feedback.lower():
            lines = final_feedback.split('\n')
            for line in lines:
                if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                    clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                    if clean_line.strip():
                        final_feedback = clean_line.strip()
                        break
        
        if not final_feedback:
            final_feedback = f"Thank you for completing the interview. Your overall score is {total_score:.2f}/1.0."
        
        return JsonResponse({
            "feedback": feedback,
            "score": score,
            "next_question": None,
            "final_feedback": final_feedback,
            "total_score": f"{total_score:.2f}"
        })

    # Generate next question based on conversation history
    next_prompt = f"""
    You are a professional interviewer for {skill}.
    Candidate Name: {session.get('name', 'Candidate')}
    
    Based on the candidate's previous answers, generate the next concise professional question.
    The conversation history so far:
    {json.dumps(history, indent=2)}
    
    Ask only one question at a time. 
    Keep it relevant to {skill} and the previous discussion.
    Make sure the question is appropriate and not too advanced.
    Keep the question concise (1 sentence maximum).
    Speak directly to the candidate.
    """
    next_question = call_ollama(next_prompt).strip()
    
    # Clean up the next question to remove any meta-text
    if "candidate:" in next_question.lower() or "interviewer:" in next_question.lower():
        lines = next_question.split('\n')
        for line in lines:
            if "interviewer:" in line.lower() or not (line.lower().startswith('candidate:') or line.lower().startswith('me:')):
                clean_line = re.sub(r'^(interviewer|me):\s*', '', line, flags=re.IGNORECASE)
                if clean_line.strip():
                    next_question = clean_line.strip()
                    break
    
    session["current_question"] = next_question
    session["question_count"] += 1

    return JsonResponse({
        "feedback": feedback,
        "score": score,
        "next_question": next_question,
        "final_feedback": None
    })