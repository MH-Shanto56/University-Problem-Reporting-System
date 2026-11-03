import math
from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=20, default='📋')

    class Meta:
        db_table = 'core_category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Issue(models.Model):
    LOCATION_TYPE_CHOICES = [
        ('room', 'Structured Room Location'),
        ('landmark', 'Landmark-Based Location'),
    ]
    RELATIVE_POSITION_CHOICES = [
        ('', '-- Select Relative Position --'),
        ('left_side', 'Left Side'),
        ('right_side', 'Right Side'),
        ('in_front_of', 'In Front Of'),
        ('behind', 'Behind'),
        ('beside', 'Beside'),
        ('before', 'Before'),
        ('after', 'After'),
        ('near', 'Near'),
        ('opposite', 'Opposite'),
        ('inside', 'Inside'),
        ('outside', 'Outside'),
        ('entrance', 'Entrance'),
        ('exit', 'Exit'),
        ('between', 'Between'),
    ]
    CATEGORY_CHOICES = [
        ('Classroom & Lab', 'Classroom & Lab (Projector, PC, AC)'),
        ('Electrical & Power', 'Electrical & Power (Lights, Fans, Outlets)'),
        ('Internet & Wi-Fi', 'Internet & Wi-Fi (Campus Network, Routers)'),
        ('Sanitation & Hygiene', 'Sanitation & Hygiene (Washrooms, Water Dispenser)'),
        ('Furniture & Fixtures', 'Furniture & Fixtures (Benches, Doors, Whiteboards)'),
        ('Safety & Security', 'Safety & Security (CCTV, Fire Extinguisher, Exit)'),
        ('Other', 'Other Campus Issues'),
    ]
    PRIORITY_CHOICES = [
        ('urgent', '🚨 Urgent'),
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Hybrid Location Fields
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, default='room')
    building = models.ForeignKey('locations.Building', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    floor = models.ForeignKey('locations.Floor', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    room = models.ForeignKey('locations.Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    landmark = models.ForeignKey('locations.Landmark', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    relative_position = models.CharField(max_length=30, choices=RELATIVE_POSITION_CHOICES, blank=True, default='')
    custom_location_description = models.CharField(max_length=300, blank=True, default='')
    normalized_location_description = models.CharField(max_length=300, blank=True, default='')
    equipment = models.ForeignKey('locations.Equipment', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    equipment_identifier = models.CharField(max_length=100, blank=True, default='', help_text="e.g. AC-01, Projector-1")
    is_ambiguous_duplicate = models.BooleanField(default=False)

    # Legacy Area & Room text support
    area = models.ForeignKey('locations.Area', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    room_number = models.CharField(
        max_length=100, blank=True, default='',
        help_text="e.g. Room 704, Software Lab 2, Game Room, Mosque, etc."
    )

    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    image = models.ImageField(upload_to='issues/%Y/%m/', blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_issues'
    )

    # Resolution & Closure Lifecycle Fields
    resolution_attempt = models.IntegerField(default=1, help_text="Repair cycle counter, increments upon reopening")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    work_report_summary = models.TextField(blank=True, default='', help_text="Details of repairs/work completed by department")
    work_technician_name = models.CharField(max_length=150, blank=True, default='', help_text="Name of technician or staff who performed repair")
    work_materials_used = models.CharField(max_length=255, blank=True, default='', help_text="Materials or parts replaced")
    work_completion_image = models.ImageField(upload_to='resolutions/%Y/%m/', blank=True, null=True, help_text="Proof photo of completed work")
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_issues'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_reason = models.TextField(blank=True, default='', help_text="Official reason recorded upon issue closure")
    
    # Reopen Management
    reopen_requested = models.BooleanField(default=False)
    reopen_reason = models.TextField(blank=True, default='')
    reopen_requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reopen_requests'
    )
    reopen_requested_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_issue'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_location_display(self):
        if self.location_type == 'room' and self.room:
            b_name = self.building.name if self.building else (self.room.floor.building.name if self.room.floor else "Main Building")
            f_name = self.floor.name if self.floor else (self.room.floor.name if self.room.floor else "")
            r_str = f"Room {self.room.room_number}" if not self.room.room_number.lower().startswith('room') else self.room.room_number
            eq_str = f" [{self.equipment_identifier}]" if self.equipment_identifier else ""
            return f"🏢 {b_name} • {f_name} • {r_str}{eq_str}"
        elif self.location_type == 'landmark' and self.landmark:
            b_name = self.building.name if self.building else "Campus"
            pos_label = self.get_relative_position_display() if self.relative_position else ""
            pos_str = f" ({pos_label})" if pos_label else ""
            f_name = f" • {self.floor.name}" if self.floor else ""
            return f"📍 {b_name}{f_name} • {self.landmark.name}{pos_str}"
        elif self.area:
            r_str = f" • {self.room_number}" if self.room_number else ""
            return f"🏢 {self.area.name}{r_str}"
        elif self.room_number:
            return f"Room {self.room_number}"
        return "Campus Location"

    def save(self, *args, **kwargs):
        if self.room:
            if not self.floor:
                self.floor = self.room.floor
            if not self.building and self.room.floor:
                self.building = self.room.floor.building
            if not self.room_number:
                self.room_number = self.room.room_number
        elif self.landmark:
            if not self.building and self.landmark.building:
                self.building = self.landmark.building
            if not self.floor and self.landmark.floor:
                self.floor = self.landmark.floor

        if (self.latitude is None or self.longitude is None) and self.building:
            self.latitude = self.building.latitude
            self.longitude = self.building.longitude

        if self.custom_location_description:
            self.normalized_location_description = self.custom_location_description.strip().lower()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            IssueStatusHistory.objects.create(
                issue=self,
                previous_status='',
                new_status='submitted',
                changed_by=self.reporter,
                reason='Initial problem report submission',
                resolution_attempt=self.resolution_attempt,
            )
            if self.status != 'submitted':
                IssueStatusHistory.objects.create(
                    issue=self,
                    previous_status='submitted',
                    new_status=self.status,
                    changed_by=self.reporter,
                    reason=f'Initial status set to {self.get_status_display()}',
                    resolution_attempt=self.resolution_attempt,
                )

    def update_status(self, new_status, changed_by, reason='', resolution_attempt=None):
        old_status = self.status
        if old_status == new_status and resolution_attempt is None:
            return None

        self.status = new_status
        if resolution_attempt is not None:
            self.resolution_attempt = resolution_attempt

        if new_status == 'resolved':
            self.resolved_by = changed_by
            self.resolved_at = timezone.now()
        elif new_status == 'closed':
            self.closed_by = changed_by
            self.closed_at = timezone.now()
            self.closure_reason = reason
        elif new_status in ['in_progress', 'submitted']:
            if old_status in ['resolved', 'closed']:
                self.reopen_requested = False

        self.save()

        history = IssueStatusHistory.objects.create(
            issue=self,
            previous_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            resolution_attempt=self.resolution_attempt,
        )
        return history

    def get_community_verification_summary(self):
        current_attempt = self.resolution_attempt
        verifs = self.verifications.filter(resolution_attempt=current_attempt)
        resolved_count = verifs.filter(verification_choice='appears_resolved').count()
        exists_count = verifs.filter(verification_choice='still_exists').count()
        total = resolved_count + exists_count

        has_conflicts = (resolved_count > 0 and exists_count > 0)

        if has_conflicts:
            summary_message = "Conflicting resolution feedback received. Department review required."
            status_indicator = "conflict"
        elif resolved_count > 0:
            summary_message = "Community feedback suggests that the problem may have been resolved. Awaiting department verification."
            status_indicator = "positive"
        elif exists_count > 0:
            summary_message = "Community feedback indicates the problem still exists. Ongoing repairs needed."
            status_indicator = "negative"
        else:
            summary_message = "No community resolution observations submitted yet."
            status_indicator = "pending"

        return {
            'resolved_count': resolved_count,
            'exists_count': exists_count,
            'total': total,
            'has_conflicts': has_conflicts,
            'summary_message': summary_message,
            'status_indicator': status_indicator,
            'recent_verifications': verifs.select_related('student')[:15],
        }

    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def latest_rework_history(self):
        """Returns latest rework request from admin if currently in progress."""
        if self.status == 'in_progress':
            return self.status_history.filter(
                previous_status='resolved',
                new_status='in_progress'
            ).order_by('-created_at').first()
        return None

    @property
    def pending_reopen_request(self):
        """Returns any pending reopen request for this issue."""
        return self.reopen_requests.filter(decision='pending').order_by('-requested_at').first()

    @property
    def priority_score(self):
        severity_weight = {'high': 30, 'medium': 15, 'low': 5}.get(self.priority, 10)
        age_hours = (timezone.now() - self.created_at).total_seconds() / 3600
        recency = max(0, 50 - math.log1p(age_hours) * 5)
        vote_score = min(self.vote_count * 2, 40)
        return round(severity_weight + recency + vote_score, 2)

    @property
    def time_ago(self):
        diff = timezone.now() - self.created_at
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        minutes = int(seconds // 60)
        if minutes < 60:
            return f'{minutes} min ago'
        hours = int(minutes // 60)
        if hours < 24:
            return f'{hours}h ago'
        days = int(hours // 24)
        if days < 7:
            return f'{days}d ago'
        weeks = int(days // 7)
        return f'{weeks}w ago'

    @property
    def all_images(self):
        """Returns list of all photo evidence (up to 3) attached to this issue."""
        photos = []
        if self.image:
            photos.append(self.image)
        for extra in self.additional_images.all():
            if extra.image:
                photos.append(extra.image)
        return photos


class IssueImage(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='issues/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_issueimage'
        ordering = ['created_at']

    def __str__(self):
        return f"Photo for Issue #{self.issue_id}"


class IssueStatusHistory(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, blank=True, default='')
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='status_changes'
    )
    reason = models.TextField(blank=True, default='')
    resolution_attempt = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_issuestatushistory'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.issue.title}: {self.previous_status} -> {self.new_status} ({self.created_at})"


class IssueReopenRequest(models.Model):
    DECISION_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='reopen_requests')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reopen_requests'
    )
    reason = models.TextField(help_text="Student reason for requesting reopen")
    requested_at = models.DateTimeField(default=timezone.now)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reopen_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='', help_text="Staff review notes or rejection reason")

    class Meta:
        db_table = 'core_issuereopenrequest'
        ordering = ['-requested_at']

    def __str__(self):
        return f"Reopen Request #{self.id} for {self.issue.title} ({self.decision})"


class ResolutionVerification(models.Model):
    CHOICES = [
        ('appears_resolved', 'Problem Appears Resolved'),
        ('still_exists', 'Problem Still Exists'),
    ]
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='verifications')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resolution_verifications'
    )
    resolution_attempt = models.IntegerField(default=1, help_text="Cycle version for which this verification was submitted")
    verification_choice = models.CharField(max_length=20, choices=CHOICES)
    comment = models.TextField(blank=True, default='', help_text="Optional student observation details")
    image = models.ImageField(upload_to='verifications/%Y/%m/', blank=True, null=True, help_text="Optional photo evidence")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_resolutionverification'
        ordering = ['-updated_at']
        unique_together = ('issue', 'student', 'resolution_attempt')

    def __str__(self):
        return f"{self.student.username} - {self.get_verification_choice_display()} on {self.issue.title}"


class Vote(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_vote'
        unique_together = ('issue', 'user')

    def __str__(self):
        return f'{self.user} -> {self.issue}'


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.issue.title}"


class Feedback(models.Model):
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE, related_name='feedback')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5, help_text="Rating 1 to 5")
    comments = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_feedback'

    def __str__(self):
        return f"Feedback for {self.issue.title} ({self.rating}★)"
