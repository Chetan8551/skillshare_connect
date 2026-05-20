def update_interview_scores(
    session,
    answer_quality
):

    if answer_quality == "strong":
        session.strong_answer_count += 1
        session.overall_score += 8

    elif answer_quality == "average":
        session.overall_score += 5

    elif answer_quality == "weak":
        session.weak_answer_count += 1
        session.overall_score += 2

    session.question_count += 1

    session.save()


def calculate_final_score(session):

    if session.question_count == 0:
        return 0

    max_possible = session.question_count * 8

    percentage = (
        session.overall_score / max_possible
    ) * 100

    return round(
        min(percentage, 100),
        2
    )