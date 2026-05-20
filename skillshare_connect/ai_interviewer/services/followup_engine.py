import re


TECH_PATTERNS = {
    "jwt": [
        "Why did you choose JWT authentication?",
        "How did you handle token expiration?",
        "What security concerns exist with JWT?"
    ],

    "django": [
        "What challenges did you face in Django?",
        "How did you structure your Django project?",
        "How did you optimize Django performance?"
    ],

    "rest api": [
        "How did you secure your APIs?",
        "How did you handle API errors?",
        "Did you implement authentication and permissions?"
    ],

    "postgresql": [
        "How did you optimize database queries?",
        "Did you use indexing?",
        "How did you design your database schema?"
    ],

    "docker": [
        "Why did you use Docker?",
        "How did you manage containers?",
        "Did you use Docker Compose?"
    ]
}


def extract_followup_topics(message):

    msg = message.lower()

    found = []

    for topic in TECH_PATTERNS.keys():

        if topic in msg:
            found.append(topic)

    return found


def generate_followup_question(message):

    topics = extract_followup_topics(message)

    if not topics:
        return None

    topic = topics[0]

    questions = TECH_PATTERNS.get(topic, [])

    if not questions:
        return None

    return questions[0]