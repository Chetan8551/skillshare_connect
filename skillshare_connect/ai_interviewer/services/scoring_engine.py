def calculate_score(answer_quality, behavior_flags):
    score = 5

    if answer_quality == "strong":
        score += 3

    elif answer_quality == "weak":
        score -= 2

    if behavior_flags.get("confident"):
        score += 1

    if behavior_flags.get("low_interest"):
        score -= 2

    if behavior_flags.get("rude"):
        score -= 5

    score = max(0, min(score, 10))

    return score