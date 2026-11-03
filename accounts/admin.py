from django.contrib import admin
from .models import UserProfile, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'department', 'assigned_department', 'points']
    list_filter = ['assigned_department', 'department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'student_id']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
