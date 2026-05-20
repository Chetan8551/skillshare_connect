import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from ai_interviewer.models import InterviewSession

from .models import Interview
from ai_interviewer.services.interview_engine import (
    process_interview_message
)


def interview_page(request):

    return render(
        request,
        "ai_interviewer/interview.html"
    )
from django.shortcuts import render

def interview_page(request):
    return render(request, 'ai_interviewer/interview.html')


def process_answer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        answer = data.get("answer")

        question = "Tell me about yourself"

        feedback = f"Good answer: {answer}"

        # ✅ SAVE TO DATABASE
        Interview.objects.create(
            user_name="Guest",
            question=question,
            answer=answer,
            feedback=feedback
        )

        return JsonResponse({
            "response": feedback
        })

@csrf_exempt
def interview_chat(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required"
            },
            status=405
        )

    try:

        data = json.loads(request.body)

        role = data.get(
            "role",
            "General Interview"
        )

        message = data.get(
            "message",
            ""
        ).strip()

        history = data.get(
            "history",
            []
        )

        session_id = data.get(
            "session_id"
        )

        # =========================
        # GET OR CREATE SESSION
        # =========================

        session = None

        if session_id:

            try:

                session = InterviewSession.objects.get(
                    id=session_id
                )

            except InterviewSession.DoesNotExist:

                session = InterviewSession.objects.create(
                    role=role
                )

        else:

            session = InterviewSession.objects.create(
                role=role
            )

        # =========================
        # PROCESS MESSAGE
        # =========================

        result = process_interview_message(
            session=session,
            candidate_message=message,
            history=history
        )

        return JsonResponse({

            "success": True,

            "session_id": session.id,

            "stage": result.get(
                "stage"
            ),

            "reply_type": result.get(
                "reply_type"
            ),

            "feedback": result.get(
                "feedback"
            ),

            "better_answer": result.get(
                "better_answer"
            ),

            "next_question": result.get(
                "next_question"
            ),

            "answer_quality": result.get(
                "answer_quality"
            ),

            "should_end": result.get(
                "should_end"
            ),

            "score": result.get(
                "score"
            )

        })

    except Exception as e:

        print("\nVIEW ERROR:")
        print(str(e))
        print("\n")

        return JsonResponse({

            "success": False,
            "error": str(e)

        })