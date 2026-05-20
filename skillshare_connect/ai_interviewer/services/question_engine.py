import random


TOPIC_FALLBACKS = [
    "projects",
    "problem solving",
    "debugging",
    "teamwork",
    "backend development",
    "system design",
    "databases",
]


def choose_difficulty(answer_quality):

    if answer_quality == "strong":
        return "hard"

    if answer_quality == "weak":
        return "easy"

    return "medium"


def extract_topics(session):

    skills = session.mentioned_skills

    if not skills:
        return TOPIC_FALLBACKS

    cleaned = [
        s.strip()
        for s in skills.split(",")
        if s.strip()
    ]

    if not cleaned:
        return TOPIC_FALLBACKS

    return cleaned


def choose_topic(session):

    topics = extract_topics(session)

    weak_topics = [
        t.strip()
        for t in session.weak_topics.split(",")
        if t.strip()
    ]

    strong_topics = [
        t.strip()
        for t in session.strong_topics.split(",")
        if t.strip()
    ]

    if weak_topics:
        return random.choice(weak_topics)

    if strong_topics:
        return random.choice(strong_topics)

    return random.choice(topics)


def generate_question_context(
    session,
    answer_quality
):
    difficulty = choose_difficulty(
        answer_quality
    )

    topic = choose_topic(session)

    return {
        "difficulty": difficulty,
        "topic": topic
    }