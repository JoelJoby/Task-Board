import json
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from .models import Task

class TaskModelTests(TestCase):
    def test_create_task_defaults(self):
        task = Task.objects.create(title="Test Task")
        self.assertEqual(task.status, 'PENDING')
        self.assertEqual(task.priority, 'MEDIUM')
        self.assertEqual(task.estimated_minutes, 30)
        self.assertFalse(task.is_currently_locked)
        self.assertIsNotNone(task.cryptic_hint)

    def test_countdown_lock(self):
        future_time = timezone.now() + timedelta(minutes=10)
        task = Task.objects.create(
            title="Locked Task",
            lock_type="COUNTDOWN",
            unlock_at=future_time,
            cryptic_hint="Time shall pass."
        )
        self.assertTrue(task.is_currently_locked)
        self.assertGreater(task.remaining_seconds, 0)

        # Unlocked task
        past_time = timezone.now() - timedelta(minutes=1)
        task.unlock_at = past_time
        task.save()
        self.assertFalse(task.is_currently_locked)
        self.assertEqual(task.remaining_seconds, 0)

    def test_code_lock(self):
        task = Task.objects.create(
            title="Passcode Task",
            lock_type="CODE",
            unlock_code="SECRET123"
        )
        self.assertTrue(task.is_currently_locked)

class TaskAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_list_and_create_tasks(self):
        # GET empty list
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['tasks']), 0)

        # POST create task
        payload = {
            'title': 'API Task',
            'description': 'Description',
            'priority': 'HIGH',
            'estimated_minutes': 45,
            'lock_type': 'NONE'
        }
        response = self.client.post('/api/tasks/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['title'], 'API Task')

    def test_complete_locked_countdown_task_fails_with_cryptic_hint(self):
        future_time = timezone.now() + timedelta(minutes=5)
        task = Task.objects.create(
            title="Time Lock Task",
            lock_type="COUNTDOWN",
            unlock_at=future_time,
            cryptic_hint="The clock must speak '00:00'."
        )

        response = self.client.post(f'/api/tasks/{task.id}/complete/')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['reason'], 'locked_time')
        self.assertEqual(data['cryptic_hint'], "The clock must speak '00:00'.")

    def test_complete_code_locked_task(self):
        task = Task.objects.create(
            title="Code Lock Task",
            lock_type="CODE",
            unlock_code="MATRIX",
            cryptic_hint="Speak the word MATRIX."
        )

        # Wrong code fails
        response = self.client.post(f'/api/tasks/{task.id}/complete/', data=json.dumps({'passcode': 'WRONG'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['reason'], 'locked_code')

        # Correct code succeeds
        response = self.client.post(f'/api/tasks/{task.id}/complete/', data=json.dumps({'passcode': 'MATRIX'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['status'], 'COMPLETED')

    def test_seed_demo_tasks(self):
        response = self.client.post('/api/tasks/seed/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['tasks']), 0)
