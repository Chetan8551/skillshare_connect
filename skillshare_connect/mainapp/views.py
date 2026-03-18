from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from mainapp.models import CustomUser, UserSkill, Skill, ConnectionRequest, Session, Review, Availability, Message
from .forms import CustomUserCreationForm, UserSkillForm, ConnectionRequestForm, SessionForm, AvailabilityForm, MessageForm
import json
import os
import random
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from collections import defaultdict

from .forms import (
    CustomUserCreationForm,
    UserSkillForm,
    ConnectionRequestForm,
    SessionForm,
    AvailabilityForm,
    MessageForm,
)
from .models import (
    CustomUser,
    UserSkill,
    Skill,
    ConnectionRequest,
    Session,
    Review,
    Availability,
    Message,
)

# JSON file path for storing user data
USER_DATA_FILE = os.path.join(settings.BASE_DIR, "user_data.json")

# ✅ Helper: Save/update user in JSON file
def save_user_to_json(user):
    data = []
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # remove old record if exists
    data = [u for u in data if u.get("username") != user.username]

    # append new record
    data.append({
        "username": user.username,
        "email": user.email,
        "password": user.password,  # hashed password
        "first_name": user.first_name,
        "last_name": user.last_name,
        "city": user.city,
        "university": user.university,
        "year_of_study": user.year_of_study,
    })

    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ✅ OTP memory store
RESET_OTP_STORE = {}

# ---------------- HOME ----------------
def home(request):
    if request.user.is_authenticated:
        greeting = f"Welcome back, {request.user.first_name or request.user.username} 👋"
    else:
        greeting = "Learn. Teach. Connect. — Join the community"

    featured_users = CustomUser.objects.annotate(
        teach_count=Count('skills', filter=Q(skills__skill_type='teach'))
    ).order_by('-teach_count')[:3]

    for u in featured_users:
        u.teach_skills = u.skills.filter(skill_type='teach')[:3]
        u.learn_skills = u.skills.filter(skill_type='learn')[:2]

    teach_skill_counts = (
        UserSkill.objects.filter(skill_type='teach')
        .values('skill')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )
    trending_skills = []
    for entry in teach_skill_counts:
        try:
            trending_skills.append((Skill.objects.get(pk=entry['skill']), entry['count']))
        except Skill.DoesNotExist:
            continue

    recent_sessions = Session.objects.filter(status='completed').order_by('-scheduled_time')[:5]
    recent_reviews = Review.objects.select_related('reviewer', 'reviewee').order_by('-created_at')[:3]

    top_teachers = CustomUser.objects.annotate(
        avg_rating=Avg('received_reviews__rating')
    ).order_by('-avg_rating')[:5]

    local_users = []
    if request.user.is_authenticated and request.user.city:
        local_users = CustomUser.objects.filter(city=request.user.city).exclude(id=request.user.id)[:5]

    upcoming_sessions = []
    if request.user.is_authenticated:
        upcoming_sessions = Session.objects.filter(
            Q(teacher=request.user) | Q(student=request.user),
            status='scheduled'
        ).order_by('scheduled_time')[:3]

    context = {
        'greeting': greeting,
        'featured_users': featured_users,
        'trending_skills': trending_skills,
        'recent_sessions': recent_sessions,
        'recent_reviews': recent_reviews,
        'top_teachers': top_teachers,
        'local_users': local_users,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'home.html', context)


# ---------------- PROFILE ----------------
@login_required
def profile(request, user_id=None):
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
    else:
        user = request.user
    
    teach_skills = user.skills.filter(skill_type='teach')
    learn_skills = user.skills.filter(skill_type='learn')
    availability = user.availability.all()
    
    connections_count = ConnectionRequest.objects.filter(
        Q(from_user=user, status='accepted') | Q(to_user=user, status='accepted')
    ).count()
    
    connection_status = None
    if request.user.is_authenticated and user_id and user_id != request.user.id:
        connection_request = ConnectionRequest.objects.filter(
            Q(from_user=request.user, to_user=user) | Q(from_user=user, to_user=request.user)
        ).first()
        
        if connection_request:
            connection_status = connection_request.status
    
    context = {
        'profile_user': user,
        'teach_skills': teach_skills,
        'learn_skills': learn_skills,
        'availability': availability,
        'connections_count': connections_count,
        'connection_status': connection_status,
    }
    return render(request, 'profile.html', context)

# ---------------- DASHBOARD ----------------


@login_required
def dashboard(request):
    now = timezone.now()

    # All sessions for this user
    user_sessions = Session.objects.filter(
        Q(teacher=request.user) | Q(student=request.user)
    )

    # Split by end_time and status
    upcoming_sessions = [
        s for s in user_sessions
        if s.end_time and s.end_time > now and s.status == "scheduled"
    ]
    completed_sessions = [
        s for s in user_sessions
        if (s.end_time and s.end_time <= now) or s.status == "completed"
    ]

    # Sort sessions
    upcoming_sessions = sorted(upcoming_sessions, key=lambda x: x.scheduled_time)[:5]
    completed_sessions = sorted(completed_sessions, key=lambda x: x.scheduled_time, reverse=True)[:5]

    # Connections
    connections = CustomUser.objects.filter(
        Q(received_requests__from_user=request.user, received_requests__status="accepted") |
        Q(sent_requests__to_user=request.user, sent_requests__status="accepted")
    ).distinct()

    # Pending requests
    pending_requests = ConnectionRequest.objects.filter(to_user=request.user, status="pending")[:5]

    # Stats
    total_connections = connections.count()
    start_of_week = now.date() - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    sessions_this_week = Session.objects.filter(
        Q(teacher=request.user) | Q(student=request.user),
        scheduled_time__date__range=[start_of_week, end_of_week]
    ).count()
    avg_rating = Review.objects.filter(reviewee=request.user).aggregate(
        avg_rating=Avg("rating")
    )["avg_rating"] or 0

    # AI recommendations
    user_learn_skills = request.user.skills.filter(skill_type="learn").values_list("skill", flat=True)
    ai_recommendations = CustomUser.objects.filter(
        skills__skill__in=user_learn_skills,
        skills__skill_type="teach"
    ).exclude(id=request.user.id).annotate(
        match_score=Count("skills", filter=Q(skills__skill__in=user_learn_skills))
    ).order_by("-match_score")[:3]

    context = {
        "connections": connections,
        "upcoming_sessions": upcoming_sessions,
        "completed_sessions": completed_sessions,
        "pending_requests": pending_requests,
        "notifications": [],
        "total_connections": total_connections,
        "sessions_this_week": sessions_this_week,
        "avg_rating": round(avg_rating, 1),
        "ai_recommendations": ai_recommendations,
    }

    return render(request, "dashboard.html", context)


# mainapp/views.py

from collections import defaultdict
from django.db.models import Q, Avg, Count, Prefetch
from django.utils import timezone
from datetime import timedelta

# -------- helpers --------
def _initials(u):
    if u.first_name or u.last_name:
        return f"{(u.first_name or '')[:1]}{(u.last_name or '')[:1]}".upper()
    return (u.username or 'U')[:2].upper()

def _humanize_last_seen(dt):
    if not dt:
        return "a while ago"
    delta = timezone.now() - dt
    s = int(delta.total_seconds())
    if s < 60: return "just now"
    m = s // 60
    if m < 60: return f"{m} min ago"
    h = m // 60
    if h < 24: return f"{h} hr ago"
    d = h // 24
    return f"{d} day{'s' if d != 1 else ''} ago"

def _time_str(t):
    s = t.strftime("%I:%M %p")
    return s.lstrip("0")

def _availability_dict(user):
    # Build { "Mon": "6–8 PM, 7–9 PM", ... }
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    by_day = defaultdict(list)
    for a in user.availability.all():
        by_day[days[a.day_of_week]].append(f"{_time_str(a.start_time)} - {_time_str(a.end_time)}")
    return {d: ", ".join(times) for d, times in by_day.items()}

def _has_availability_overlap(u1, u2):
    # crude but fast: overlapping time windows on the same weekday
    a1 = defaultdict(list)
    for a in u1.availability.all():
        a1[a.day_of_week].append((a.start_time, a.end_time))
    for b in u2.availability.all():
        for s, e in a1.get(b.day_of_week, []):
            if max(s, b.start_time) < min(e, b.end_time):
                return True
    return False

@login_required
def matches(request):
    me = request.user

    candidates = (
        CustomUser.objects
        .exclude(id=me.id)
        .prefetch_related(
            Prefetch('skills', queryset=UserSkill.objects.select_related('skill')),
            'availability',
            'received_reviews',
            'teaching_sessions',
            'learning_sessions'
        )
        .annotate(
            avg_rating=Avg('received_reviews__rating'),
            review_count=Count('received_reviews', distinct=True),
            completed_as_teacher=Count('teaching_sessions',
                                       filter=Q(teaching_sessions__status='completed'),
                                       distinct=True),
            completed_as_student=Count('learning_sessions',
                                       filter=Q(learning_sessions__status='completed'),
                                       distinct=True),
        )
    )

    my_teach = set(me.skills.filter(skill_type='teach').values_list('skill__name', flat=True))
    my_learn = set(me.skills.filter(skill_type='learn').values_list('skill__name', flat=True))

    cards = []
    for u in candidates:
        teach = [us.skill.name for us in u.skills.all() if us.skill_type == 'teach']
        learn = [us.skill.name for us in u.skills.all() if us.skill_type == 'learn']

        teach_set, learn_set = set(teach), set(learn)

        they_can_teach_me = my_learn & teach_set
        they_want_what_I_teach = my_teach & learn_set

        score = 0.0
        denom = max(len(my_teach) + len(my_learn), 1)
        skill_points = (2 * len(they_can_teach_me) + 1.5 * len(they_want_what_I_teach)) / denom
        score += min(60.0, 60.0 * skill_points)

        rating = (u.avg_rating or 0.0)
        score += 25.0 * (rating / 5.0)

        total_completed = int(u.completed_as_teacher or 0) + int(u.completed_as_student or 0)
        score += 10.0 * min(total_completed, 10) / 10.0

        if _has_availability_overlap(me, u):
            score += 5.0

        percentage = int(round(min(score, 99)))

        reasons = []
        if they_can_teach_me:
            reasons.append("Can teach " + ", ".join(sorted(they_can_teach_me)))
        if they_want_what_I_teach:
            reasons.append("Wants to learn " + ", ".join(sorted(they_want_what_I_teach)))
        reason = " • ".join(reasons) if reasons else "Similar interests and skill match"

        cards.append({
            "id": u.id,
            "name": u.get_full_name() or u.username,
            "initials": _initials(u),
            "university": u.university,
            "year": u.year_of_study,
            "major": u.bio[:100] + ("…" if u.bio and len(u.bio) > 100 else ""),
            "city": u.city,
            "rating": round(rating or 0.0, 1),
            "reviews": int(u.review_count or 0),
            "sessions": total_completed,
            "percentage": percentage,
            "online": bool(u.last_login and (timezone.now() - u.last_login) < timedelta(minutes=10)),
            "last_seen": _humanize_last_seen(u.last_login),
            "can_teach": teach,
            "wants_to_learn": learn,
            "availability": _availability_dict(u),
            "reason": reason,
        })

    # ✅ Apply filters from query params
    filter_type = request.GET.get("filter")

    if filter_type == "online":
        cards = [c for c in cards if c["online"]]

    elif filter_type == "nearby":
        # simple nearby: same university (adjust if you have city/location field)
        cards = [c for c in cards if c["city"] and c["city"].lower() == me.city.lower()]

    elif filter_type == "active":
        # sort by most active (sessions) first
        cards.sort(key=lambda x: (-x["sessions"], -x["rating"], -x["percentage"], x["name"].lower()))

    else:
        # default: best match %
        cards = [c for c in cards if c["percentage"] > 0]  # remove 0% matches
        cards.sort(key=lambda x: (-x["percentage"], -x["rating"], -x["sessions"], x["name"].lower()))

    return render(request, "matches.html", {"matches": cards, "filter": filter_type})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import CustomUser

# ---------------- AUTH ----------------
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
                return redirect('auth')

        elif form_type == 'signup':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            university = request.POST.get('university')
            year_of_study = request.POST.get('year_of_study')
            city = request.POST.get('city')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return redirect('auth')

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('auth')

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
                return redirect('auth')

            try:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    university=university,
                    year_of_study=year_of_study,
                    city=city
                )

                # ✅ Save user in JSON
                save_user_to_json(user, plaintext_password=password1)

                # ✅ Send email confirmation
                send_mail(
                    subject="Account Created Successfully",
                    message=f"Hi {user.first_name}, you have successfully created an account on our website!",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )

                login(request, user)
                messages.success(request, 'Account created successfully! Please check your email.')
                return redirect('profile')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('auth')

    return render(request, 'auth.html')

# In-memory OTP store
import random

# In-memory OTP store
RESET_OTP_STORE = {}

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = random.randint(100000, 999999)
            RESET_OTP_STORE[email] = otp

            send_mail(
                subject="Password Reset OTP",
                message=f"Your OTP for password reset is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
            messages.success(request, "OTP sent to your email. Please verify it next.")
            request.session['reset_email'] = email
            return redirect('verify_otp')
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, 'forgot_password.html')


def verify_otp(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Please enter your email first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if str(RESET_OTP_STORE.get(email)) == str(otp_input):
            messages.success(request, "OTP verified! Set your new password now.")
            request.session['otp_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP. Try again.")

    return render(request, 'verify_otp.html')


def reset_password(request):
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified', False)

    if not email or not otp_verified:
        messages.error(request, "You need to verify OTP first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                user = CustomUser.objects.get(email=email)
                user.set_password(password1)
                user.save()

                # ✅ Update JSON file with new plain password
                save_user_to_json(user, plaintext_password=password1)

                # Clear session and OTP
                RESET_OTP_STORE.pop(email, None)
                request.session.pop('reset_email', None)
                request.session.pop('otp_verified', None)

                messages.success(request, "Password reset successful! You can login now.")
                return redirect('auth')
            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")

    return render(request, 'reset_password.html')



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser, UserSkill, Skill

@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        # Update personal info (same as before)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.university = request.POST.get("university", user.university)
        user.year_of_study = request.POST.get("year_of_study", user.year_of_study)
        user.city = request.POST.get("city", user.city)
        user.bio = request.POST.get("bio", user.bio)

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        user.save()

        # Handle skills
        teach_skills = request.POST.getlist("teach_skills[]")
        teach_proficiencies = request.POST.getlist("teach_proficiencies[]")
        learn_skills = request.POST.getlist("learn_skills[]")
        learn_proficiencies = request.POST.getlist("learn_proficiencies[]")

        # Clear old skills
        UserSkill.objects.filter(user=user).delete()

        # Save teach skills
        for skill_name, proficiency in zip(teach_skills, teach_proficiencies):
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": "Other"}  # ✅ if new skill, set category as "Other"
            )
            UserSkill.objects.create(
                user=user,
                skill=skill,
                proficiency=proficiency,
                skill_type="teach"
            )

        # Save learn skills
        for skill_name, proficiency in zip(learn_skills, learn_proficiencies):
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": "Other"}
            )
            UserSkill.objects.create(
                user=user,
                skill=skill,
                proficiency=proficiency,
                skill_type="learn"
            )

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    # Preload skills
    teach_skills = UserSkill.objects.filter(user=user, skill_type="teach")
    learn_skills = UserSkill.objects.filter(user=user, skill_type="learn")
    all_skills = Skill.objects.all()

    return render(
        request,
        "edit_profile.html",
        {
            "user": user,
            "teach_skills": teach_skills,
            "learn_skills": learn_skills,
            "all_skills": all_skills,
        },
    )

from django.shortcuts import render
from django.db.models import Q
from .models import CustomUser, Skill

def search_profiles(request):
    query = request.GET.get('q', '')
    skill_filter = request.GET.get('skill', '')

    users = CustomUser.objects.all()

    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(university__icontains=query) |
            Q(skills__skill__name__icontains=query)
        ).distinct()

    if skill_filter:
        users = users.filter(skills__skill__name__icontains=skill_filter).distinct()

    context = {
        'query': query,
        'skill_filter': skill_filter,
        'all_skills': Skill.objects.all(),
        'users': users,   # ✅ MUST BE "users" to match search.html
    }
    return render(request, 'search.html', context)



@login_required
def add_skill(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST)
        if form.is_valid():
            user_skill = form.save(commit=False)
            user_skill.user = request.user
            user_skill.save()
            return redirect('profile')
    else:
        form = UserSkillForm()
    
    return render(request, 'add_skill.html', {'form': form})

@login_required
def send_connection_request(request, user_id):
    to_user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if a request already exists
    existing_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=to_user
    ).first()
    
    if existing_request:
        # Request already exists
        messages.info(request, f'You have already sent a connection request to {to_user.get_full_name()}')
        return redirect('profile_view', user_id=user_id)  # Fixed this line
    
    if request.method == 'POST':
        form = ConnectionRequestForm(request.POST)
        if form.is_valid():
            connection_request = form.save(commit=False)
            connection_request.from_user = request.user
            connection_request.to_user = to_user
            connection_request.save()
            messages.success(request, f'Connection request sent to {to_user.get_full_name()}')
            return redirect('profile_view', user_id=user_id)  # Fixed this line
    else:
        form = ConnectionRequestForm()
    
    return render(request, 'connection_request.html', {'form': form, 'to_user': to_user})

@login_required
def respond_to_connection_request(request, request_id, response):
    connection_request = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user)
    
    if response == 'accept':
        connection_request.status = 'accepted'
        messages.success(request, f'You are now connected with {connection_request.from_user.get_full_name()}')
        
        # Create a notification message
        Message.objects.create(
            sender=request.user,
            receiver=connection_request.from_user,
            connection=connection_request,
            content=f"I've accepted your connection request! Let's schedule a session."
        )
        
    elif response == 'reject':
        connection_request.status = 'rejected'
        messages.info(request, f'Connection request from {connection_request.from_user.get_full_name()} rejected')
    
    connection_request.save()
    return redirect('dashboard')

@login_required
def schedule_session(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if users are connected
    are_connected = ConnectionRequest.objects.filter(
        Q(from_user=request.user, to_user=other_user, status='accepted') |
        Q(from_user=other_user, to_user=request.user, status='accepted')
    ).exists()
    
    if not are_connected:
        messages.error(request, 'You need to be connected to schedule a session')
        return redirect('profile_view', user_id=user_id)
    
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            
            # Determine who is teaching and who is learning based on skills
            skill = form.cleaned_data['skill']
            user_can_teach = request.user.skills.filter(skill=skill, skill_type='teach').exists()
            other_can_teach = other_user.skills.filter(skill=skill, skill_type='teach').exists()
            
            if user_can_teach and not other_can_teach:
                session.teacher = request.user
                session.student = other_user
            elif other_can_teach and not user_can_teach:
                session.teacher = other_user
                session.student = request.user
            else:
                # Both can teach, need to specify who is teaching
                # For simplicity, let's assume the current user is teaching
                session.teacher = request.user
                session.student = other_user
            
            session.save()
            messages.success(request, 'Session scheduled successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SessionForm()
    
    return render(request, 'schedule_session.html', {'form': form, 'other_user': other_user})

def search_users(request):
    query = request.GET.get('q', '')
    skill_filter = request.GET.get('skill', '')
    
    users = CustomUser.objects.all()
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(university__icontains=query)
        )
    
    if skill_filter:
        users = users.filter(skills__skill__name__icontains=skill_filter)
    
    # Get distinct users
    users = users.distinct()
    
    # Get all skills for the filter dropdown
    all_skills = Skill.objects.all()
    
    context = {
        'users': users,
        'query': query,
        'skill_filter': skill_filter,
        'all_skills': all_skills,
    }
    return render(request, 'search.html', context)

@login_required
def api_user_matches(request):
    # API endpoint for AJAX requests to get user matches
    skill_id = request.GET.get('skill_id')
    
    if skill_id:
        # Find users who can teach this skill
        matches = CustomUser.objects.filter(
            skills__skill__id=skill_id,
            skills__skill_type='teach'
        ).exclude(id=request.user.id).annotate(
            avg_rating=Avg('received_reviews__rating')
        ).order_by('-avg_rating')[:10]
        
        data = [
            {
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'university': user.university,
                'rating': user.avg_rating or 0,
                'skills': list(user.skills.filter(skill_type='teach').values_list('skill__name', flat=True))
            }
            for user in matches
        ]
        
        return JsonResponse(data, safe=False)
    
    return JsonResponse([], safe=False)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def messages_view(request, connection_id=None):
    """
    Shows all connections and the selected chat. 
    Also shows unread counts per connection for sidebar display.
    """
    # all accepted connections where user is a participant
    connections = ConnectionRequest.objects.filter(
        Q(from_user=request.user, status='accepted') |
        Q(to_user=request.user, status='accepted')
    ).distinct().select_related('from_user', 'to_user').prefetch_related('messages')

    selected_connection = None
    connection_messages = []

    if connection_id:
        selected_connection = get_object_or_404(ConnectionRequest, id=connection_id)

        # safety: ensure user is participant
        if selected_connection.from_user != request.user and selected_connection.to_user != request.user:
            return redirect('messages')

        connection_messages = Message.objects.filter(connection=selected_connection).order_by('timestamp')

        # 👇 mark unread messages as read when opening this chat
        connection_messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    # handle POST (send message)
    if request.method == 'POST' and selected_connection:
        form = MessageForm(request.POST)
        if 'content' in form.fields:
            form.fields['content'].widget.attrs.update({
                'class': 'flex-1 px-4 py-2 rounded-full border border-gray-300 dark:border-gray-700 '
                         'dark:bg-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-green-400 focus:outline-none',
                'placeholder': 'Type a message...'
            })
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = (selected_connection.to_user if selected_connection.from_user == request.user
                            else selected_connection.from_user)
            msg.connection = selected_connection
            msg.save()
            return redirect('messages', connection_id=connection_id)
    else:
        form = MessageForm()
        if 'content' in form.fields:
            form.fields['content'].widget.attrs.update({
                'class': 'flex-1 px-4 py-2 rounded-full border border-gray-300 dark:border-gray-700 '
                         'dark:bg-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-green-400 focus:outline-none',
                'placeholder': 'Type a message...'
            })

    # 👇 unread count per connection (for sidebar like WhatsApp)
    unread_counts = {}
    for conn in connections:
        other_user = conn.to_user if conn.from_user == request.user else conn.from_user
        count = conn.messages.filter(receiver=request.user, is_read=False, sender=other_user).count()
        unread_counts[conn.id] = count

    context = {
        'connections': connections,
        'selected_connection': selected_connection,
        'messages': connection_messages,
        'form': form,
        'unread_counts': unread_counts,
    }
    return render(request, 'messages.html', context)

@login_required
def start_video_call(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if users are connected
    are_connected = ConnectionRequest.objects.filter(
        Q(from_user=request.user, to_user=other_user, status='accepted') |
        Q(from_user=other_user, to_user=request.user, status='accepted')
    ).exists()
    
    if not are_connected:
        messages.error(request, 'You need to be connected to start a video call')
        return redirect('profile', user_id=user_id)
    
    # Generate a unique room ID (using a simple approach)
    room_id = f"skillshare_{request.user.id}_{other_user.id}_{int(timezone.now().timestamp())}"
    
    context = {
        'other_user': other_user,
        'room_id': room_id,
    }
    return render(request, 'video_call.html', context)

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # Check if user is part of this session
    if session.teacher != request.user and session.student != request.user:
        messages.error(request, 'You do not have access to this session')
        return redirect('dashboard')
    
    # Get reviews if any
    try:
        review = Review.objects.get(session=session)
    except Review.DoesNotExist:
        review = None
    
    context = {
        'session': session,
        'review': review,
    }
    return render(request, 'session_detail.html', context)

@login_required
def add_review(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # Check if user can review this session (must be the student)
    if session.student != request.user:
        messages.error(request, 'Only the student can review this session')
        return redirect('dashboard')
    
    # Check if review already exists
    if hasattr(session, 'review'):
        messages.info(request, 'You have already reviewed this session')
        return redirect('session_detail', session_id=session_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                session=session,
                reviewer=request.user,
                reviewee=session.teacher,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review added successfully')
            return redirect('session_detail', session_id=session_id)
        else:
            messages.error(request, 'Please provide both rating and comment')
    
    return render(request, 'add_review.html', {'session': session})



import json
import os
from django.conf import settings

USER_JSON_PATH = os.path.join(settings.BASE_DIR, 'user_data.json')

def save_user_to_json(user, plaintext_password=None):
    """
    Save or update a user in user_data.json.
    Stores hashed password and optional plaintext password.
    """
    # Load existing data
    if os.path.exists(USER_JSON_PATH):
        with open(USER_JSON_PATH, 'r') as f:
            try:
                data = json.load(f)
                # Ensure it's a dictionary, not a list
                if isinstance(data, list):
                    # Convert list to dict keyed by username
                    temp = {}
                    for u in data:
                        temp[u['username']] = u
                    data = temp
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    # Update/add user
    data[user.username] = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password_hashed": user.password,
        "password_plain": plaintext_password if plaintext_password else "",  # store plaintext if given
        "university": getattr(user, 'university', ''),
        "year_of_study": getattr(user, 'year_of_study', ''),
        "city": getattr(user, 'city', ''),
    }

    # Save back to JSON
    with open(USER_JSON_PATH, 'w') as f:
        json.dump(data, f, indent=4)

