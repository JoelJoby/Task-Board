from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/tasks/', views.api_tasks, name='api_tasks'),
    path('api/tasks/<int:task_id>/complete/', views.api_complete_task, name='api_complete_task'),
    path('api/tasks/<int:task_id>/delete/', views.api_delete_task, name='api_delete_task'),
    path('api/tasks/seed/', views.api_seed_demo, name='api_seed_demo'),
]
