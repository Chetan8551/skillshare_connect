import json
import re


def extract_json(text):

    text = text.strip()

    try:
        return json.loads(text)

    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:

        possible_json = match.group(0)

        try:
            return json.loads(
                possible_json
            )

        except Exception:
            pass

    return {
        "stage": "conversation",
        "intent": "connect",
        "reply_type": "conversation",
        "feedback": "I'm having a little trouble understanding your response right now.",
        "better_answer": "",
        "next_question": "Could you tell me a bit about yourself?",
        "answer_quality": "none",
        "should_end": False,
        "parse_failed": True
    }