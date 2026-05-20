import json

from ai_interviewer.models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer
)

from .ollama_service import generate_ai_response
from .response_parser import extract_json

from .behavior_analyzer import (
    analyze_behavior,
    detect_obvious_weak_answer
)

from .scoring_engine import calculate_score

from .stage_manager import determine_stage

from .memory_engine import update_memory

from .question_engine import (
    generate_question_context
)

from .followup_engine import (
    generate_followup_question
)

from .question_guard import (
    is_repeated_question
)

from .interview_scorer import (
    update_interview_scores,
    calculate_final_score
)

from .interview_ending import (
    should_end_interview
)

from .final_feedback import (
    generate_final_feedback
)

from ai_interviewer.interviewer_prompt import (
    build_prompt
)


def process_interview_message(
    session,
    candidate_message,
    history
):

    behavior_flags = analyze_behavior(
        candidate_message,
        history
    )

    question_context = generate_question_context(
        session,
        "average"
    )

    prompt = build_prompt(
        role=session.role,
        candidate_message=candidate_message,
        history=history,
        session=session,
        question_context=question_context
    )

    raw_response = generate_ai_response(
        prompt
    )

    print("\n" + "=" * 50)
    print("RAW LLM RESPONSE:")
    print(raw_response)
    print("=" * 50 + "\n")

    parsed = extract_json(
        raw_response
    )

    reply_type = parsed.get(
        "reply_type",
        "conversation"
    )

    answer_quality = parsed.get(
        "answer_quality",
        "none"
    )
    if not answer_quality or answer_quality == "none":

        if detect_obvious_weak_answer(
            candidate_message
        ):
            answer_quality = "weak"

        elif len(candidate_message.split()) > 25:
            answer_quality = "strong"

        else:
            answer_quality = "average"

    # =========================
    # BACKEND QUALITY OVERRIDE
    # =========================

    if detect_obvious_weak_answer(
        candidate_message
    ):
        answer_quality = "weak"

    score = 0

    next_stage = session.current_stage

    # =========================
    # INTERVIEW PROGRESSION
    # =========================

    session.question_count += 1

    score = calculate_score(
        answer_quality,
        behavior_flags
    )

    update_interview_scores(
        session,
        answer_quality
    )

    next_stage = determine_stage(
        session,
        answer_quality
    )

    session.current_stage = next_stage

    session.overall_score = round(
        (
            session.overall_score + score
        ) / 2,
        2
    )

    if answer_quality == "strong":

        session.strong_answer_count += 1

    elif answer_quality == "weak":

        session.weak_answer_count += 1

    session.conversation_turns += 1
    # =========================
    # MEMORY UPDATE
    # =========================

    update_memory(
        session,
        candidate_message,
        answer_quality
    )

    question_context = generate_question_context(
        session,
        answer_quality
    )

    followup_question = generate_followup_question(
        candidate_message
    )

    question_text = (
        followup_question
        or parsed.get("next_question", "")
    )

    # =========================
    # QUESTION DEDUPLICATION
    # =========================

    if is_repeated_question(
        history,
        question_text
    ):

        question_text = (
            "Let's explore a different area. "
            + parsed.get(
                "next_question",
                ""
            )
        )

    session.save()

    # =========================
    # SAVE QUESTION
    # =========================

    question = InterviewQuestion.objects.create(
        session=session,
        question_text=question_text,
        stage=next_stage
    )

    # =========================
    # SAVE ANSWER
    # =========================

    InterviewAnswer.objects.create(
        question=question,
        answer_text=candidate_message,
        feedback=parsed.get(
            "feedback",
            ""
        ),
        better_answer=parsed.get(
            "better_answer",
            ""
        ),
        answer_quality=answer_quality,
        score=score
    )

    # =========================
    # DEBUG LOGGING
    # =========================

    print("\n")
    print("QUESTION COUNT:", session.question_count)
    print("STRONG ANSWERS:", session.strong_answer_count)
    print("WEAK ANSWERS:", session.weak_answer_count)
    print("CURRENT STAGE:", session.current_stage)
    print("OVERALL SCORE:", session.overall_score)
    print("\n")

    # =========================
    # INTERVIEW ENDING LOGIC
    # =========================

    llm_requested_end = parsed.get(
        "should_end",
        False
    )

    auto_end = should_end_interview(
        session
    )

    print("AUTO END:", auto_end)

    if llm_requested_end or auto_end:

        session.interview_completed = True

        final_score = calculate_final_score(
            session
        )

        session.final_score = final_score

        final_feedback = generate_final_feedback(
            session
        )

        session.final_feedback = final_feedback

        session.save()

        return {
            "success": True,
            "stage": "end",
            "reply_type": "end",
            "feedback": final_feedback,
            "better_answer": "",
            "next_question": "",
            "answer_quality": "none",
            "should_end": True,
            "score": final_score
        }

    return {
        "success": True,
        "stage": next_stage,
        "reply_type": reply_type,
        "feedback": parsed.get(
            "feedback",
            ""
        ),
        "better_answer": parsed.get(
            "better_answer",
            ""
        ),
        "next_question": question_text,
        "answer_quality": answer_quality,
        "should_end": False,
        "score": score,
        "question_context": question_context
    }