from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks_page, name='tasks'),

    # API
    path('api/tasks/', views.api_tasks, name='api_tasks'),
    path('api/tasks/create/', views.api_create_task, name='api_create_task'),
    path('api/tasks/<int:task_id>/complete/', views.api_complete_task, name='api_complete_task'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
