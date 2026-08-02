import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .services import create_task, get_tasks, complete_task, get_stats
from .models import Task, Profile


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                error = 'Invalid username or password.'

    return render(request, 'tasks/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# Page views  (all protected)
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    stats = get_stats()
    profile = Profile.get_profile()
    return render(request, 'tasks/dashboard.html', {
        'stats': stats,
        'active_page': 'dashboard',
        'profile': profile,
    })


@login_required
def tasks_page(request):
    profile = Profile.get_profile()
    return render(request, 'tasks/tasks.html', {
        'active_page': 'tasks',
        'profile': profile,
    })


# ---------------------------------------------------------------------------
# API: List tasks
# ---------------------------------------------------------------------------

@login_required
def api_tasks(request):
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search = request.GET.get('search', '')

    qs = get_tasks(
        status_filter=status_filter or None,
        priority_filter=priority_filter or None,
        search=search or None,
    )

    now = timezone.now()
    tasks_data = []
    for task in qs:
        effective_status = task.get_current_status()

        # Persist status updates (lock expired → pending, odd-minute → expired)
        if effective_status != task.status and task.status not in ('completed',):
            task.status = effective_status
            task.save(update_fields=['status'])

        # Compute deadline info (odd-minute tasks only)
        deadline = task.deadline
        deadline_ts = deadline.isoformat() if deadline else None

        # Compute lock remaining seconds
        lock_remaining = None
        if effective_status == 'locked' and task.locked_until:
            diff = (task.locked_until - now).total_seconds()
            lock_remaining = max(0, int(diff))

        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'priority': task.priority,
            'estimated_time': task.estimated_time,
            'created_at': task.created_at.isoformat(),
            'status': effective_status,
            'locked_until': task.locked_until.isoformat() if task.locked_until else None,
            'lock_remaining': lock_remaining,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'deadline': deadline_ts,
            'is_odd_minute': task.created_at.minute % 2 != 0,
        })

    # Apply status filter after computing effective status
    if status_filter:
        tasks_data = [t for t in tasks_data if t['status'] == status_filter]

    return JsonResponse({'tasks': tasks_data})


# ---------------------------------------------------------------------------
# API: Create task
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
@require_http_methods(['POST'])
def api_create_task(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

    title = data.get('title', '').strip()
    priority = data.get('priority', '').strip().lower()
    estimated_time = data.get('estimated_time', 0)

    # Validation
    errors = {}
    if not title:
        errors['title'] = 'Title is required.'
    if priority not in ('low', 'medium', 'high'):
        errors['priority'] = 'Priority must be Low, Medium, or High.'
    try:
        estimated_time = int(estimated_time)
        if estimated_time <= 0:
            errors['estimated_time'] = 'Estimated time must be greater than 0.'
    except (ValueError, TypeError):
        errors['estimated_time'] = 'Estimated time must be a number.'

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    task = create_task(title=title, priority=priority, estimated_time=estimated_time)

    now = timezone.now()
    deadline = task.deadline
    lock_remaining = None
    if task.status == 'locked' and task.locked_until:
        diff = (task.locked_until - now).total_seconds()
        lock_remaining = max(0, int(diff))

    return JsonResponse({
        'success': True,
        'message': 'Task created successfully.',
        'task': {
            'id': task.id,
            'title': task.title,
            'priority': task.priority,
            'estimated_time': task.estimated_time,
            'created_at': task.created_at.isoformat(),
            'status': task.status,
            'locked_until': task.locked_until.isoformat() if task.locked_until else None,
            'lock_remaining': lock_remaining,
            'deadline': deadline.isoformat() if deadline else None,
            'is_odd_minute': task.created_at.minute % 2 != 0,
        },
    }, status=201)


# ---------------------------------------------------------------------------
# API: Complete task
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
@require_http_methods(['POST'])
def api_complete_task(request, task_id):
    success, message, hint = complete_task(task_id)
    response_data = {
        'success': success,
        'message': message,
    }
    if hint:
        response_data['hint'] = hint
    status_code = 200 if success else 400
    return JsonResponse(response_data, status=status_code)


# ---------------------------------------------------------------------------
# API: Stats
# ---------------------------------------------------------------------------

@login_required
def api_stats(request):
    return JsonResponse(get_stats())


# ---------------------------------------------------------------------------
# Profile: Edit
# ---------------------------------------------------------------------------

@login_required
def edit_profile(request):
    profile = Profile.get_profile()
    user = request.user
    errors = {}

    if request.method == 'POST':
        # --- Profile fields ---
        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip()
        phone    = request.POST.get('phone', '').strip()
        age_raw  = request.POST.get('age', '').strip()
        dob_raw  = request.POST.get('dob', '').strip()

        # --- Account fields ---
        new_username = request.POST.get('username', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # --- Validation: profile ---
        if not name:
            errors['name'] = 'Name is required.'

        age = None
        if age_raw:
            try:
                age = int(age_raw)
                if age <= 0 or age > 120:
                    errors['age'] = 'Enter a valid age (1–120).'
            except ValueError:
                errors['age'] = 'Age must be a number.'

        dob = None
        if dob_raw:
            from datetime import date
            try:
                dob = date.fromisoformat(dob_raw)
            except ValueError:
                errors['dob'] = 'Enter a valid date.'

        # --- Validation: username ---
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not new_username:
            errors['username'] = 'Username is required.'
        elif new_username != user.username:
            if User.objects.exclude(pk=user.pk).filter(username=new_username).exists():
                errors['username'] = 'That username is already taken.'

        # --- Validation: password (optional — only if filled) ---
        if new_password or confirm_password:
            if len(new_password) < 6:
                errors['new_password'] = 'Password must be at least 6 characters.'
            elif new_password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            # Save profile
            profile.name  = name
            profile.email = email
            profile.phone = phone
            profile.age   = age
            profile.dob   = dob
            profile.save()

            # Save username
            if new_username and new_username != user.username:
                user.username = new_username
                user.save(update_fields=['username'])

            # Save password (only if provided)
            if new_password:
                user.set_password(new_password)
                user.save(update_fields=['password'])
                # Re-authenticate so session stays valid after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

            return redirect('/profile/edit/?saved=1')

    return render(request, 'tasks/edit_profile.html', {
        'profile': profile,
        'user': user,
        'errors': errors,
        'active_page': '',
    })
