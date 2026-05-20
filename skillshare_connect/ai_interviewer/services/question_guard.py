def is_repeated_question(
    history,
    question
):

    if not question:
        return False

    q = question.lower().strip()

    for item in history:

        if item.get(
            "sender"
        ) != "interviewer":
            continue

        text = item.get(
            "text",
            ""
        ).lower()

        if q in text:
            return True

    return False