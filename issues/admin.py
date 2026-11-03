from django.contrib import admin
from .models import (
    Category, Issue, IssueImage, IssueStatusHistory, IssueReopenRequest,
    ResolutionVerification, Vote, Comment, Feedback
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'icon']
    list_filter = ['department']
    search_fields = ['name']

class IssueImageInline(admin.TabularInline):
    model = IssueImage
    extra = 1

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'location_type', 'building', 'floor', 'room', 'priority', 'status', 'resolution_attempt', 'reporter', 'created_at']
    list_filter = ['status', 'priority', 'category', 'location_type', 'building', 'reopen_requested', 'created_at']
    search_fields = ['title', 'description', 'room__room_number', 'room_number', 'custom_location_description', 'reporter__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'closed_at']
    inlines = [IssueImageInline]

@admin.register(IssueImage)
class IssueImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'issue', 'image', 'created_at']
    search_fields = ['issue__title']

@admin.register(IssueStatusHistory)
class IssueStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['issue', 'previous_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['issue__title', 'changed_by__username', 'reason']

@admin.register(IssueReopenRequest)
class IssueReopenRequestAdmin(admin.ModelAdmin):
    list_display = ['issue', 'requester', 'decision', 'requested_at', 'reviewer']
    list_filter = ['decision', 'requested_at']
    search_fields = ['issue__title', 'requester__username', 'reason']

@admin.register(ResolutionVerification)
class ResolutionVerificationAdmin(admin.ModelAdmin):
    list_display = ['issue', 'student', 'verification_choice', 'created_at']
    list_filter = ['verification_choice', 'created_at']
    search_fields = ['issue__title', 'student__username', 'comment']

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['issue', 'user', 'created_at']
    search_fields = ['issue__title', 'user__username']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'user', 'created_at']
    search_fields = ['issue__title', 'user__username', 'content']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['issue', 'student', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['issue__title', 'student__username', 'comments']
