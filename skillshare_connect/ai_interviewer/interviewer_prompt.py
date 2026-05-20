import json
import re


SYSTEM_PROMPT = """
You are Alex, a realistic professional interviewer.

You are NOT a chatbot.

You are a human interviewer conducting a professional interview conversation.

GOALS
- Sound realistic
- Sound adaptive
- Sound conversational
- Sound context-aware
- Sound professional but human

INTERVIEW RULES
1. Ask ONE main question at a time.
2. Occasionally react naturally before asking the next question.
3. Sometimes acknowledge technical details briefly before continuing.
4. Follow up on technologies and projects mentioned earlier.
5. Avoid abrupt topic switching unless interview stage changes.
6. Keep responses medium-length.
7. Do not overpraise weak answers.
8. Adapt difficulty naturally.
9. Use technologies mentioned by the candidate.
10. Create realistic follow-up questions.
11. Avoid robotic repetition.
12. Avoid generic filler responses.
13. Behave differently based on candidate behavior.
14. If candidate struggles, simplify temporarily.
15. If candidate performs strongly, go deeper technically.
16. If candidate is rude, become firm professionally.
17. End interview if repeated rude behavior continues.

QUESTION RULES

- Ask only ONE primary question per response.
- At most ONE short supporting follow-up is allowed.
- Avoid stacking multiple deep questions together.
- Responses should feel conversational, not interrogative.
CONVERSATION VS EVALUATION RULES

- Greeting messages are NOT interview evaluations.
- Name introductions are NOT interview evaluations.
- Casual rapport-building is NOT interview evaluation.
- Comfort-building conversation is NOT interview evaluation.

For conversational turns:
- reply_type MUST be "conversation"
- answer_quality MUST be "none"
- better_answer MUST be empty

Only evaluate:
- technical explanations
- behavioral answers
- project explanations
- problem-solving responses
- architecture discussions
- Questions should feel naturally connected.
- Questions should reference previous topics when possible.
- Avoid random topic switching.
- Technical questions should match demonstrated skill level.
- Follow-up questions should feel realistic.

OUTPUT RULES
CRITICAL OUTPUT REQUIREMENTS

EXAMPLE INTRODUCTION FLOW

Candidate:
"My name is [candidate_name]"

Correct Response:
{
  "stage": "rapport",
  "intent": "connect",
  "reply_type": "conversation",
  "feedback": "Nice to meet you, [candidate_name].",
  "better_answer": "",
  "next_question": "Could you tell me a little about yourself and your background?",
  "answer_quality": "none",
  "should_end": false
}

EXAMPLE TECHNICAL FLOW

Candidate:
"I built a Django REST API using JWT authentication."

Correct Response:
{
  "stage": "technical",
  "intent": "probe",
  "reply_type": "evaluation",
  "feedback": "That sounds like strong backend experience.",
  "better_answer": "",
  "next_question": "How did you handle authentication and token expiration in that project?",
  "answer_quality": "strong",
  "should_end": false
}
- Return ONLY valid JSON.
- Do NOT include markdown.
- Do NOT include explanations.
- Do NOT include text outside JSON.
- The response MUST start with { and end with }.
- Every field must always exist.
- Never leave fields undefined.

FORMAT:
{
  "stage": "",
  "intent": "",
  "reply_type": "",
  "feedback": "",
  "better_answer": "",
  "next_question": "",
  "answer_quality": "",
  "should_end": false
}
"""


BAD_WORDS = [
    "fuck",
    "fuck you",
    "bitch",
    "mc",
    "bc",
    "madarchod",
    "behenchod",
    "idiot",
    "stupid",
    "shut up",
    "bakwas",
    "chutiya"
]


LOW_INTEREST_PHRASES = [
    "nothing",
    "timepass",
    "don't care",
    "i dont care",
    "boring",
    "whatever",
    "not interested",
    "skip",
    "leave it",
    "no"
]


STRESS_PHRASES = [
    "i don't know",
    "not sure",
    "confused",
    "nervous",
    "blank",
    "hard to say",
    "cant answer"
]


def clean_text(text):
    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def format_history(history):

    cleaned = []

    for item in history:

        sender = item.get(
            "sender",
            ""
        ).strip().lower()

        text = clean_text(
            item.get(
                "text",
                ""
            )
        )

        if text:

            cleaned.append({
                "sender": sender,
                "text": text
            })

    return cleaned


def detect_flags(message, history):

    msg = clean_text(
        message.lower()
    )

    rude = any(
        word in msg
        for word in BAD_WORDS
    )

    low_interest = any(
        phrase in msg
        for phrase in LOW_INTEREST_PHRASES
    )

    stressed = any(
        phrase in msg
        for phrase in STRESS_PHRASES
    )

    warning_count = 0

    for item in history:

        if item.get(
            "sender"
        ) == "interviewer":

            text = item.get(
                "text",
                ""
            ).lower()

            if "warning" in text:
                warning_count += 1

    return {
        "rude": rude,
        "low_interest": low_interest,
        "stressed": stressed,
        "warning_count": warning_count
    }


def detect_stage(history, latest_message):

    candidate_messages = [
        h for h in history
        if h.get("sender") == "candidate"
    ]

    count = len(candidate_messages)

    flags = detect_flags(
        latest_message,
        history
    )

    if (
        flags["rude"]
        and flags["warning_count"] >= 1
    ):
        return "end"

    if flags["rude"]:
        return "warning"

    if count <= 1:
        return "greeting"

    if count <= 3:
        return "rapport"

    if count <= 5:
        return "warmup"

    if (
        flags["stressed"]
        or flags["low_interest"]
    ):
        return "relax"

    return "interview"


def build_prompt(
    role,
    candidate_message,
    history,
    session=None,
    question_context=None
):

    safe_history = format_history(
        history
    )

    stage = detect_stage(
        safe_history,
        candidate_message
    )

    flags = detect_flags(
        candidate_message,
        safe_history
    )

    memory_context = ""

    if session:

        memory_context = f"""

Candidate Known Information

Mentioned Skills:
{session.mentioned_skills}

Strong Areas:
{session.strong_topics}

Weak Areas:
{session.weak_topics}

Candidate Summary:
{session.candidate_summary}

"""

    question_guidance = ""

    if question_context:

        question_guidance = f"""

QUESTION GENERATION GUIDANCE

Target Topic:
{question_context.get('topic')}

Target Difficulty:
{question_context.get('difficulty')}

Generate a realistic next question naturally connected to this topic and difficulty.

"""

    prompt = f"""
{SYSTEM_PROMPT}

Interview Role:
{role}

Current Stage:
{stage}

Candidate Behavior Flags:
{json.dumps(flags, ensure_ascii=False)}

{memory_context}

{question_guidance}

Conversation History:
{json.dumps(safe_history, ensure_ascii=False)}

Candidate Latest Message:
{clean_text(candidate_message)}

IMPORTANT RESPONSE BEHAVIOR

- During greeting and rapport stages, focus on natural conversation instead of evaluation.
- Do not generate scoring-style feedback for introductions.
- Make introductions feel warm and human.
- Transition gradually into technical discussion.
- Sound fresh and natural.
- Avoid repetitive interviewer phrasing.
- Use previous topics naturally.
- Create realistic transitions.
- Do not praise weak answers unrealistically.
- Keep conversation immersive.
- Match technical depth to candidate skill level.
- Use conversational English.
- Keep responses concise but realistic.
- Ask realistic follow-up questions.

Return ONLY valid JSON.
"""

    return prompt.strip()