"""
Task business rules service.
All backend rules are enforced here — never trust frontend for these.
"""

from django.utils import timezone
from .models import Task


# ---------------------------------------------------------------------------
# Create Task
# ---------------------------------------------------------------------------

def create_task(title: str, priority: str, estimated_time: int) -> Task:
    """
    Create a new task, applying the 3-tasks-in-2-minutes locking rule.
    """
    now = timezone.now()
    two_minutes_ago = now - timezone.timedelta(minutes=2)

    recent_count = Task.objects.filter(created_at__gte=two_minutes_ago).count()

    status = 'pending'
    locked_until = None

    if recent_count >= 3:
        status = 'locked'
        locked_until = now + timezone.timedelta(minutes=5)

    task = Task.objects.create(
        title=title,
        priority=priority,
        estimated_time=estimated_time,
        created_at=now,
        status=status,
        locked_until=locked_until,
    )
    return task


# ---------------------------------------------------------------------------
# Get Tasks
# ---------------------------------------------------------------------------

def get_tasks(status_filter=None, priority_filter=None, search=None):
    """Return tasks with optional filters."""
    qs = Task.objects.all()
    if priority_filter:
        qs = qs.filter(priority=priority_filter)
    if search:
        qs = qs.filter(title__icontains=search)
    return qs


# ---------------------------------------------------------------------------
# Complete Task
# ---------------------------------------------------------------------------

CRYPTIC_HINTS = {
    'high_priority': "The path begins below.",
    'hidden_logic': "Some doors open only after another has been passed.",
    'locked': "This gate is sealed for now.",
    'expired': "Time has already passed this door by.",
    'already_done': "This journey has already reached its end.",
}


def _can_complete_task(task: Task):
    """
    Hidden completion logic gate.
    Returns (allowed: bool, hint_key: str | None)
    """
    now = timezone.now()

    # Sync effective status
    effective_status = task.get_current_status()

    if effective_status == 'completed':
        return False, 'already_done'

    if effective_status == 'locked':
        return False, 'locked'

    if effective_status == 'expired':
        return False, 'expired'

    # Rule 1 — High priority task requires at least one completed Low priority task
    if task.priority == 'high':
        has_completed_low = Task.objects.filter(
            priority='low', status='completed'
        ).exists()
        if not has_completed_low:
            return False, 'high_priority'

    # Hidden logic: task id must not be a multiple of 7
    # (This is intentionally obscure — the user will never see the reason)
    if task.id % 7 == 0:
        return False, 'hidden_logic'

    return True, None


def complete_task(task_id: int):
    """
    Attempt to complete a task.
    Returns (success: bool, message: str, hint: str | None)
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return False, 'Task not found.', None

    # Sync status for locked tasks that have expired their lock
    effective_status = task.get_current_status()
    if effective_status == 'expired' and task.status != 'expired':
        task.status = 'expired'
        task.save(update_fields=['status'])

    allowed, hint_key = _can_complete_task(task)

    if not allowed:
        hint = CRYPTIC_HINTS.get(hint_key, 'An unknown force prevents this.')
        return False, 'Completion failed.', hint

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])
    return True, 'Task completed successfully.', None


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

def get_stats():
    now = timezone.now()
    all_tasks = Task.objects.all()

    total = all_tasks.count()
    completed = all_tasks.filter(status='completed').count()

    # Count effective locked (still within lock window)
    locked = sum(
        1 for t in all_tasks.filter(status='locked')
        if t.locked_until and now < t.locked_until
    )

    # Count effective pending (not locked, not expired, not completed)
    pending = 0
    expired = 0
    for t in all_tasks.exclude(status='completed'):
        eff = t.get_current_status()
        if eff == 'pending':
            pending += 1
        elif eff == 'expired':
            expired += 1

    return {
        'total': total,
        'pending': pending,
        'completed': completed,
        'locked': locked,
        'expired': expired,
    }
