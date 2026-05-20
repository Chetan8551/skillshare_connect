def should_end_interview(session):

    if session.question_count >= 25:
        return True

    if session.weak_answer_count >= 8:
        return True

    if (
        session.current_stage == "final"
        and session.question_count >= 15
    ):
        return True

    return False