import json
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Task, DEFAULT_HINTS
import random

def index_view(request):
    return render(request, 'tasks/index.html')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_tasks(request):
    if request.method == "GET":
        tasks = Task.objects.all().order_by('-created_at')
        return JsonResponse({
            'success': True,
            'tasks': [task.to_dict() for task in tasks]
        })
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'error': 'Task title is required.'}, status=400)
            
            priority = data.get('priority', 'MEDIUM')
            if priority not in dict(Task.PRIORITY_CHOICES):
                priority = 'MEDIUM'
                
            estimated_minutes = int(data.get('estimated_minutes', 30))
            description = data.get('description', '').strip()
            lock_type = data.get('lock_type', 'NONE')
            if lock_type not in dict(Task.LOCK_TYPE_CHOICES):
                lock_type = 'NONE'
                
            unlock_at = None
            if lock_type == 'COUNTDOWN':
                minutes = int(data.get('countdown_minutes', 5))
                unlock_at = timezone.now() + timedelta(minutes=max(1, minutes))
                
            unlock_code = data.get('unlock_code', '').strip()
            cryptic_hint = data.get('cryptic_hint', '').strip()
            
            task = Task.objects.create(
                title=title,
                description=description,
                priority=priority,
                estimated_minutes=estimated_minutes,
                lock_type=lock_type,
                unlock_at=unlock_at,
                unlock_code=unlock_code,
                cryptic_hint=cryptic_hint,
                status='PENDING'
            )
            return JsonResponse({'success': True, 'task': task.to_dict()})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def api_complete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found.'}, status=404)
    
    if task.status == 'COMPLETED':
        return JsonResponse({'success': True, 'task': task.to_dict()})

    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = {}

    passcode = data.get('passcode', '').strip()

    # Check lock status
    if task.lock_type == 'COUNTDOWN' and task.unlock_at and timezone.now() < task.unlock_at:
        return JsonResponse({
            'success': False,
            'reason': 'locked_time',
            'cryptic_hint': task.cryptic_hint or random.choice(DEFAULT_HINTS),
            'remaining_seconds': task.remaining_seconds
        }, status=400)
    
    if task.lock_type == 'CODE':
        if not passcode or passcode.lower() != task.unlock_code.lower():
            return JsonResponse({
                'success': False,
                'reason': 'locked_code',
                'cryptic_hint': task.cryptic_hint or random.choice(DEFAULT_HINTS),
                'requires_passcode': True
            }, status=400)

    # Success - mark completed
    task.status = 'COMPLETED'
    task.completed_at = timezone.now()
    task.save()

    return JsonResponse({'success': True, 'task': task.to_dict()})

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def api_delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'success': True})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found.'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def api_seed_demo(request):
    # Optionally clear existing or seed sample tasks
    demo_tasks = [
        {
            "title": "Quantum Encryption Upgrade",
            "description": "Deploy key rotation protocols across all subterranean servers.",
            "priority": "URGENT",
            "estimated_minutes": 45,
            "lock_type": "NONE",
            "cryptic_hint": "The quantum field stabilizes with immediate execution."
        },
        {
            "title": "Decrypt Chronos Protocol Logs",
            "description": "Extract temporal anomalies from Sector 7 databanks.",
            "priority": "HIGH",
            "estimated_minutes": 60,
            "lock_type": "COUNTDOWN",
            "countdown_minutes": 3,
            "cryptic_hint": "Patience is a key written in shadow. The clock must speak '00:00' before the seal dissolves."
        },
        {
            "title": "Bypass Neural Firewall Cipher",
            "description": "Bypass security grid using the matrix security passphrase.",
            "priority": "HIGH",
            "estimated_minutes": 90,
            "lock_type": "CODE",
            "unlock_code": "CYBER2026",
            "cryptic_hint": "A secret phrase rests in the void. Speak the lost word 'CYBER2026' to shatter the seal."
        },
        {
            "title": "Sync Sub-Orbital Telemetry",
            "description": "Align satellite antenna grid with deep space beacon.",
            "priority": "MEDIUM",
            "estimated_minutes": 20,
            "lock_type": "NONE",
            "cryptic_hint": "Telemetry sync complete."
        },
        {
            "title": "Calibrate Void Engine Cores",
            "description": "Perform safety sweep on anti-matter containment thrusters.",
            "priority": "LOW",
            "estimated_minutes": 15,
            "lock_type": "COUNTDOWN",
            "countdown_minutes": 10,
            "cryptic_hint": "The ancient hourglass still drips with sand. Do not rush destiny."
        }
    ]

    created = []
    for dt in demo_tasks:
        unlock_at = None
        if dt.get('lock_type') == 'COUNTDOWN':
            unlock_at = timezone.now() + timedelta(minutes=dt.get('countdown_minutes', 5))
        
        t = Task.objects.create(
            title=dt['title'],
            description=dt['description'],
            priority=dt['priority'],
            estimated_minutes=dt['estimated_minutes'],
            lock_type=dt['lock_type'],
            unlock_at=unlock_at,
            unlock_code=dt.get('unlock_code', ''),
            cryptic_hint=dt['cryptic_hint'],
            status='PENDING'
        )
        created.append(t.to_dict())

    return JsonResponse({'success': True, 'tasks': created})
