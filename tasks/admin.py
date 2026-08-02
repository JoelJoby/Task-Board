from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'estimated_time', 'status', 'created_at', 'locked_until', 'completed_at']
    list_filter = ['status', 'priority']
    search_fields = ['title']
    ordering = ['-created_at']
