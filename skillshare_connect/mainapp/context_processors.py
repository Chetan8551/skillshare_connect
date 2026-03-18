from .models import Message

def unread_messages(request):
    """
    Makes unread_count available in all templates.
    """
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {"unread_count": unread_count}
    return {"unread_count": 0}
