import re


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
    "no interest",
    "not interested",
    "leave it",
    "skip",
    "noo",
    "no"
]


STRESS_PHRASES = [
    "i don't know",
    "i dont know",
    "not sure",
    "confused",
    "nervous",
    "difficult",
    "hard to say",
    "can't answer",
    "cant answer",
    "blank"
]


CONFIDENCE_PHRASES = [
    "i built",
    "i developed",
    "i created",
    "i implemented",
    "i solved",
    "i improved",
]

WEAK_SHORT_RESPONSES = [
    "i don't know",
    "dont know",
    "not sure",
    "i dont remember",
    "don't remember",
    "no idea",
    "can't remember",
    "cant remember",
    "idk"
]


def detect_obvious_weak_answer(
    message
):

    msg = message.lower().strip()

    if len(msg.split()) <= 3:
        return True

    if any(
        p in msg
        for p in WEAK_SHORT_RESPONSES
    ):
        return True

    return False
def clean_text(text):
    return re.sub(r"\\s+", " ", text).strip().lower()


def analyze_behavior(message, history):
    msg = clean_text(message)

    rude = any(word in msg for word in BAD_WORDS)

    low_interest = any(
        phrase in msg
        for phrase in LOW_INTEREST_PHRASES
    )

    stressed = any(
        phrase in msg
        for phrase in STRESS_PHRASES
    )

    confident = any(
        phrase in msg
        for phrase in CONFIDENCE_PHRASES
    )

    short_answer = len(msg.split()) <= 3

    long_answer = len(msg.split()) >= 80

    warning_count = 0

    for item in history:
        if item.get("sender") == "interviewer":
            text = item.get("text", "").lower()

            if "warning" in text:
                warning_count += 1

    return {
        "rude": rude,
        "low_interest": low_interest,
        "stressed": stressed,
        "confident": confident,
        "short_answer": short_answer,
        "long_answer": long_answer,
        "warning_count": warning_count
    }