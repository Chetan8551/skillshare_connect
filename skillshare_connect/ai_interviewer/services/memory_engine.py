TECH_KEYWORDS = [
    "django",
    "python",
    "rest api",
    "drf",
    "jwt",
    "sql",
    "postgresql",
    "javascript",
    "react",
    "docker",
    "machine learning",
    "tensorflow",
    "api",
    "authentication",
    "html",
    "css",
    "django",
    "python",
    "rest api",
    "drf",
    "jwt",
    "sql",
    "postgresql",
    "javascript",
    "react",
    "docker",
    "machine learning",
    "tensorflow",
    "api",
    "authentication",
    "html",
    "css",
    "git",
    "github",
    "node.js",
    "flask",
    "bootstrap",
    "mongodb",
    "mysql",
    "redis",
    "ci/cd",
    "aws",
    "azure",
    "kubernetes",
    "microservices",
    "debugging",
    "testing",
    "deployment",
    "version control",
    "agile",
    "data structures",
    "algorithms",
    "object-oriented programming",
    "security",
    "encryption",
    "authorization",
    "crud",
    "full stack",
    "frontend",
    "backend",
    "user interface",
    "user experience"
]
PROJECT_PATTERNS = [
    "built",
    "developed",
    "created",
    "implemented",
    "designed"
]


def update_memory(session, candidate_message, answer_quality):

    msg = candidate_message.lower()

    found_skills = []

    for skill in TECH_KEYWORDS:
        if skill in msg:
            found_skills.append(skill)

    existing_skills = session.mentioned_skills.lower()

    for skill in found_skills:
        if skill not in existing_skills:
            session.mentioned_skills += f"{skill}, "

    if answer_quality == "strong":
        for skill in found_skills:
            if skill not in session.strong_topics.lower():
                session.strong_topics += f"{skill}, "

    if answer_quality == "weak":
        for skill in found_skills:
            if skill not in session.weak_topics.lower():
                session.weak_topics += f"{skill}, "
    for pattern in PROJECT_PATTERNS:

        if pattern in msg:

            summary = (
                session.candidate_summary
                + f"Candidate mentioned project work involving: {candidate_message}\n"
            )

            session.candidate_summary = summary[:3000]

            break
    session.save()