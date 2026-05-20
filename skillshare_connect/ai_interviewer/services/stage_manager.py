INTERVIEW_STAGES = [
    "intro",
    "rapport",
    "background",
    "technical_basic",
    "technical_intermediate",
    "technical_advanced",
    "behavioral",
    "situational",
    "final"
]


def determine_stage(
    session,
    answer_quality
):

    question_count = session.question_count

    strong_answers = session.strong_answer_count

    weak_answers = session.weak_answer_count

    # =========================
    # FORCE FINAL STAGE
    # =========================

    if question_count >= 18:
        return "final"

    # =========================
    # EARLY TERMINATION FLOW
    # =========================

    if weak_answers >= 8 and question_count >= 10:
        return "final"

    # =========================
    # INTRODUCTION PHASE
    # =========================

    if question_count <= 2:
        return "rapport"

    # =========================
    # BACKGROUND PHASE
    # =========================

    if question_count <= 5:
        return "background"

    # =========================
    # TECHNICAL BASIC
    # =========================

    if question_count <= 8:

        if strong_answers >= 3:
            return "technical_intermediate"

        return "technical_basic"

    # =========================
    # TECHNICAL INTERMEDIATE
    # =========================

    if question_count <= 12:

        if strong_answers >= 6:
            return "technical_advanced"

        if weak_answers >= 5:
            return "technical_basic"

        return "technical_intermediate"

    # =========================
    # TECHNICAL ADVANCED
    # =========================

    if question_count <= 14:

        if weak_answers >= 7:
            return "behavioral"

        return "technical_advanced"

    # =========================
    # BEHAVIORAL ROUND
    # =========================

    if question_count <= 16:
        return "behavioral"

    # =========================
    # SITUATIONAL ROUND
    # =========================

    if question_count <= 18:
        return "situational"

    # =========================
    # FINAL
    # =========================

    return "final"