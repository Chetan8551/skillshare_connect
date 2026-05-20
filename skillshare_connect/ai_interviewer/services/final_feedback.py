def generate_final_feedback(session):

    score = session.final_score

    strengths = []
    weaknesses = []

    strong_topics = [
        s.strip()
        for s in session.strong_topics.split(",")
        if s.strip()
    ]

    weak_topics = [
        s.strip()
        for s in session.weak_topics.split(",")
        if s.strip()
    ]

    if strong_topics:
        strengths.append(
            f"Strong understanding of {', '.join(strong_topics[:3])}"
        )

    if weak_topics:
        weaknesses.append(
            f"Needs improvement in {', '.join(weak_topics[:3])}"
        )

    if score >= 80:

        verdict = (
            "Excellent performance overall. "
            "You demonstrated strong technical understanding, "
            "good communication skills, and solid problem-solving ability."
        )

    elif score >= 60:

        verdict = (
            "Good overall performance with some areas for improvement. "
            "You showed decent understanding but could improve depth and confidence in certain topics."
        )

    else:

        verdict = (
            "The interview showed foundational understanding, "
            "but there are important areas that need improvement before becoming industry-ready."
        )

    feedback = f"""
Final Score: {score}/100

Overall Evaluation:
{verdict}

Strengths:
- {'; '.join(strengths) if strengths else 'Still developing technical strengths.'}

Areas to Improve:
- {'; '.join(weaknesses) if weaknesses else 'Needs more practical project experience.'}

Recommendation:
Continue practicing real-world projects, communication, and technical problem-solving consistently.
"""

    return feedback.strip()