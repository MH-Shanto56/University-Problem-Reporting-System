from django.db import models
from django.conf import settings

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField()
    issue = models.ForeignKey('issues.Issue', on_delete=models.CASCADE, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_notification'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    student_id = models.CharField(max_length=50, blank=True, default='', help_text="e.g. 24101102")
    department = models.CharField(max_length=100, blank=True, default='CSE', help_text="e.g. CSE, EEE, Pharmacy")
    assigned_department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_profiles',
        help_text="Official department assignment for staff members"
    )
    bio = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    points = models.IntegerField(default=0)

    class Meta:
        db_table = 'core_userprofile'

    def __str__(self):
        return self.user.username

    def get_effective_department(self):
        if self.assigned_department_id:
            return self.assigned_department
        if self.department:
            from departments.models import Department
            dept_str = self.department.strip()
            return Department.objects.filter(
                models.Q(code__iexact=dept_str) | models.Q(name__iexact=dept_str)
            ).first()
        return None

    @property
    def reports_count(self):
        return self.user.reported_issues.count()

    @property
    def validated_count(self):
        if hasattr(self.user, 'votes'):
            return self.user.votes.count()
        if hasattr(self.user, 'vote_set'):
            return self.user.vote_set.count()
        return 0

    @property
    def verification_count(self):
        return self.user.resolution_verifications.count()

    @property
    def badges_earned(self):
        badges = []
        if self.reports_count >= 1:
            badges.append({'name': 'First Report', 'icon': '🎯', 'color': 'orange'})
        if self.validated_count >= 5:
            badges.append({'name': 'Validator', 'icon': '✅', 'color': 'green'})
        if self.reports_count >= 10:
            badges.append({'name': 'Community Hero', 'icon': '🦸', 'color': 'blue'})
        if self.reports_count >= 25:
            badges.append({'name': 'Campus Champion', 'icon': '🏆', 'color': 'pink'})
        if self.user.reported_issues.exclude(image='').count() >= 5:
            badges.append({'name': 'Photo Pro', 'icon': '📸', 'color': 'red'})
        if self.reports_count >= 3:
            badges.append({'name': 'Quick Reporter', 'icon': '⚡', 'color': 'purple'})
        return badges

    @property
    def rank(self):
        return UserProfile.objects.filter(points__gt=self.points).count() + 1
