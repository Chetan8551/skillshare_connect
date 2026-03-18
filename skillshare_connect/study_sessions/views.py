from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField
from mainapp.models import Session
from .serializers import SessionSerializer, SessionCreateSerializer

class UpcomingSessionsList(generics.ListAPIView):
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()
        # authoritative: ensure statuses are up-to-date for the API as well
        end_expr = ExpressionWrapper(F("scheduled_time") + F("duration"), output_field=DateTimeField())
        Session.objects.filter(status="scheduled").annotate(_end=end_expr).filter(_end__lte=now).update(status="completed")
        return (Session.objects
                .filter(status="scheduled", scheduled_time__gte=now)
                .order_by("scheduled_time"))

class SessionDetail(generics.RetrieveAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

class CreateSession(generics.CreateAPIView):
    serializer_class = SessionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cancel_session(request, pk):
    try:
        session = Session.objects.get(pk=pk)
    except Session.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if session.teacher != request.user and session.student != request.user:
        return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
    if session.status != "scheduled":
        return Response({"detail": "Session already finished or cancelled"}, status=status.HTTP_400_BAD_REQUEST)
    session.status = "cancelled"
    session.save()
    return Response({"detail":"cancelled"}, status=status.HTTP_200_OK)
