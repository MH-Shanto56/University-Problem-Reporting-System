import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import models
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from .models import (
    Issue, Vote, Category, Comment, Feedback,
    IssueStatusHistory, ResolutionVerification, IssueReopenRequest, IssueImage
)
from .forms import (
    IssueForm, ResolutionVerificationForm, StatusUpdateForm,
    IssueClosureForm, IssueReopenForm
)
from locations.models import Building, Floor, Room, Landmark, Equipment, Area
from departments.models import Department
from accounts.models import UserProfile, Notification


# ==============================================================================
# 1. SIMPLE IF/ELSE DUPLICATE DETECTION (NO MODELS, NO NLP)
# ==============================================================================

def check_simple_duplicate(cleaned_data):
    """
    Pure simple if/else duplicate check (NO AI, NO NLP, NO complex algorithm).
    Checks active issues (status in 'submitted', 'in_progress').
    Returns (confirmed_duplicate_dict_or_None, list_of_ambiguous_dicts).
    """
    category = cleaned_data.get('category')
    building = cleaned_data.get('building')
    floor = cleaned_data.get('floor')
    room = cleaned_data.get('room')
    landmark = cleaned_data.get('landmark')
    title = (cleaned_data.get('title') or '').strip().lower()

    if not building:
        return None, []

    # Get active issues in the same building
    active_issues = Issue.objects.filter(
        building=building,
        status__in=['submitted', 'in_progress']
    ).select_related('room', 'landmark', 'department')

    # 1. Exact duplicate check: Room + Category match
    if room and category:
        for candidate in active_issues:
            if candidate.room_id == room.id and candidate.category == category:
                return {
                    'issue': candidate,
                    'similarity': 100,
                    'is_confirmed': True,
                    'reason': f"An active report already exists for room {room.room_number} in the same category."
                }, []

    # 2. Exact duplicate check: Landmark + Category match
    if landmark and category:
        for candidate in active_issues:
            if candidate.landmark_id == landmark.id and candidate.category == category:
                return {
                    'issue': candidate,
                    'similarity': 100,
                    'is_confirmed': True,
                    'reason': f"An active report already exists for landmark '{landmark.name}' in the same category."
                }, []

    # 3. Ambiguous/possible duplicate check: Same floor/category + title keywords
    ambiguous_matches = []
    if title:
        words = [w for w in title.split() if len(w) > 3]
        for candidate in active_issues:
            cand_title = candidate.title.lower()
            is_same_floor = (floor and candidate.floor_id == floor.id)
            is_same_cat = (candidate.category == category)

            if is_same_floor or is_same_cat:
                matches = sum(1 for w in words if w in cand_title)
                if matches >= 2 or (matches >= 1 and len(words) <= 2):
                    ambiguous_matches.append({
                        'issue': candidate,
                        'similarity': 80 if is_same_cat else 60,
                        'is_confirmed': False,
                        'reason': f"Similar active report in the same area: '{candidate.title}'"
                    })
                    if len(ambiguous_matches) >= 5:
                        break

    return None, ambiguous_matches


# ==============================================================================
# 2. PERMISSIONS & AUTHORIZATION HELPERS (MERGED IN VIEWS)
# ==============================================================================

def get_user_department(user):
    """
    Returns the Department instance assigned to a staff user, or None.
    Fails closed: if user is not authenticated, has no profile, or has no valid
    department assignment, returns None. Never crashes.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        profile = getattr(user, 'profile', None)
        if not profile:
            return None
        if hasattr(profile, 'get_effective_department'):
            return profile.get_effective_department()
        return getattr(profile, 'assigned_department', None)
    except Exception:
        return None


def user_can_manage_issue(user, issue):
    """
    Central permission helper enforcing department-level authorization:
    - Superusers may manage all issues.
    - Department staff (is_staff=True) may manage ONLY issues assigned to their authorized department.
    - Unassigned staff members are DENIED department-specific access by default (never fails open).
    - Students / non-staff users are DENIED (return False).
    - If an issue has no assigned department, only superusers can manage it.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    if not getattr(user, 'is_staff', False):
        return False
    if not issue or not getattr(issue, 'department', None):
        return False

    try:
        user_dept = get_user_department(user)
        if not user_dept:
            return False
        return user_dept.id == issue.department.id
    except Exception:
        return False


def can_user_manage_issue(user, issue):
    """Alias for user_can_manage_issue for 100% backward compatibility."""
    return user_can_manage_issue(user, issue)


def get_department_staff_recipients(issue):
    """
    Returns a queryset of User accounts authorized to receive department-scoped alerts for an issue.
    Includes:
    - Superusers (who oversee all departments)
    - Staff members explicitly assigned to issue.department (via assigned_department FK or department code/name matching)
    Excludes unrelated department staff and unassigned staff.
    """
    if not issue or not getattr(issue, 'department', None):
        return User.objects.filter(is_superuser=True)

    try:
        dept = issue.department
        return User.objects.filter(
            Q(is_superuser=True) |
            (
                Q(is_staff=True) &
                (
                    Q(profile__assigned_department=dept) |
                    Q(profile__department__iexact=dept.code) |
                    Q(profile__department__iexact=dept.name)
                )
            )
        ).distinct()
    except Exception:
        return User.objects.filter(is_superuser=True)


def get_dept_staff_users(issue):
    """Alias for get_department_staff_recipients for 100% backward compatibility."""
    return get_department_staff_recipients(issue)


# ==============================================================================
# CONTEXT PROCESSOR (NOTIFICATION CONTEXT IN VIEWS - CRASH SAFE)
# ==============================================================================

def notification_context(request):
    """
    Global context processor providing unread notification counts,
    recent notification items, and pending admin counts to all templates.
    Wrapped in try-except so it never crashes even under edge cases.
    """
    data = {
        'unread_notification_count': 0,
        'header_notifications': [],
        'pending_submitted_count': 0,
        'pending_reopens_count': 0,
    }
    try:
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            data['unread_notification_count'] = Notification.objects.filter(user=user, is_read=False).count()
            data['header_notifications'] = Notification.objects.filter(user=user).select_related('issue').order_by('-created_at')[:8]
            if user.is_staff or user.is_superuser:
                data['pending_submitted_count'] = Issue.objects.filter(status='submitted').count()
                data['pending_reopens_count'] = IssueReopenRequest.objects.filter(decision='pending').count()
    except Exception:
        pass
    return data


# ==============================================================================
# 3. PUBLIC & STUDENT VIEWS
# ==============================================================================

def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_staff:
            return redirect('department_dashboard')

    features = [
        {
            'icon': 'location',
            'title': 'Hybrid Location Intelligence',
            'desc': 'Structured room hierarchy (Building → Floor → Room) and flexible indoor landmark navigation.',
            'color': 'blue'
        },
        {
            'icon': 'camera',
            'title': 'Photo Evidence & Tracking',
            'desc': 'Upload photographic proof of issues and follow real-time progress from submission to resolution.',
            'color': 'pink'
        },
        {
            'icon': 'trending',
            'title': 'Smart Department Routing',
            'desc': 'Intelligent routing to responsible departments with simple duplicate detection.',
            'color': 'blue'
        },
        {
            'icon': 'shield',
            'title': 'Confidential & Public Reports',
            'desc': 'Submit sensitive concerns privately to authorized university staff or post publicly for student support.',
            'color': 'green'
        },
        {
            'icon': 'community',
            'title': 'Community Resolution Verification',
            'desc': 'Any student observing a repaired issue can confirm resolution, preventing premature issue closures.',
            'color': 'orange'
        },
        {
            'icon': 'chart',
            'title': 'Community Support & Urgent Ranking',
            'desc': 'Upvote critical campus issues to rank urgent problems at the top for accelerated department action.',
            'color': 'purple'
        },
    ]
    return render(request, 'home.html', {'features': features})


def about_view(request):
    return render(request, 'about.html')


def dashboard_view(request):
    """Campus Problem Explorer & Student Dashboard with Support-based Urgent Ranking."""
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()
    department_filter = request.GET.get('department', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    building_filter = request.GET.get('building', '').strip()
    search_query = request.GET.get('q', '').strip()
    # Default sort is 'support' (Most supported / urgent appears at the top)
    sort_by = request.GET.get('sort', 'support').strip()
    if not sort_by:
        sort_by = 'support'

    issues = Issue.objects.all().select_related(
        'room__floor__building', 'landmark__building', 'floor__building', 'reporter', 'department'
    ).prefetch_related('votes')

    # Privacy filtering: Students see public reports + their own private reports
    if request.user.is_authenticated:
        if not (request.user.is_staff or request.user.is_superuser):
            issues = issues.filter(Q(visibility='public') | Q(reporter=request.user))
    else:
        issues = issues.filter(visibility='public')

    if category_filter and category_filter != 'all':
        issues = issues.filter(category=category_filter)
    if status_filter and status_filter != 'all':
        issues = issues.filter(status=status_filter)
    if department_filter and department_filter != 'all':
        issues = issues.filter(department_id=department_filter)
    if priority_filter and priority_filter != 'all':
        issues = issues.filter(priority=priority_filter)
    if building_filter and building_filter != 'all':
        issues = issues.filter(building_id=building_filter)

    if search_query:
        issues = issues.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(room__room_number__icontains=search_query) |
            Q(building__name__icontains=search_query) |
            Q(landmark__name__icontains=search_query)
        )

    # Annotate total supports / votes
    issues = issues.annotate(num_votes=Count('votes'))

    # Sort ordering: Most supported comes first like urgent!
    if sort_by == 'newest':
        issues = issues.order_by('-created_at')
    elif sort_by == 'priority':
        issues = issues.order_by(
            Case(
                When(priority='high', then=3),
                When(priority='medium', then=2),
                default=1,
                output_field=IntegerField()
            ).desc(),
            '-num_votes',
            '-created_at'
        )
    elif sort_by == 'oldest':
        issues = issues.order_by('created_at')
    else:
        # Default: Most Supported / Urgent First
        sort_by = 'support'
        issues = issues.order_by('-num_votes', '-created_at')

    paginator = Paginator(issues, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    buildings = Building.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.all().order_by('name')
    areas = Area.objects.all()
    categories = [c[0] for c in Issue.CATEGORY_CHOICES]

    # Quick Stats
    all_issues = Issue.objects.all()
    stats = {
        'total': all_issues.count(),
        'in_progress': all_issues.filter(status='in_progress').count(),
        'resolved': all_issues.filter(status='resolved').count(),
        'closed': all_issues.filter(status='closed').count(),
        'high_priority': all_issues.filter(priority='high', status__in=['submitted', 'in_progress']).count(),
    }

    user_voted_issue_ids = []
    if request.user.is_authenticated:
        user_voted_issue_ids = list(request.user.votes.values_list('issue_id', flat=True))

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,
        'issues': page_obj,
        'buildings': buildings,
        'departments': departments,
        'areas': areas,
        'categories': categories,
        'stats': stats,
        'user_voted_issue_ids': user_voted_issue_ids,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'priority_filter': priority_filter,
        'building_filter': building_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'active_page': 'dashboard',
    })


@login_required
def report_issue_view(request):
    """Report Campus Problem with Simple If/Else Duplicate Check."""
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned = form.cleaned_data

            # Simple If/Else Duplicate Check
            confirmed_dup, ambiguous_dups = check_simple_duplicate(cleaned)

            if confirmed_dup:
                return render(request, 'report_problem.html', {
                    'form': form,
                    'confirmed_duplicate': confirmed_dup,
                    'buildings': Building.objects.filter(is_active=True),
                    'landmarks': Landmark.objects.filter(is_active=True),
                    'categories': [c[0] for c in Issue.CATEGORY_CHOICES],
                    'active_page': 'report',
                })

            if ambiguous_dups and not request.POST.get('confirm_not_duplicate'):
                return render(request, 'report_problem.html', {
                    'form': form,
                    'ambiguous_duplicates': ambiguous_dups,
                    'buildings': Building.objects.filter(is_active=True),
                    'landmarks': Landmark.objects.filter(is_active=True),
                    'categories': [c[0] for c in Issue.CATEGORY_CHOICES],
                    'active_page': 'report',
                })

            issue = form.save(commit=False)
            issue.reporter = request.user
            if ambiguous_dups:
                issue.is_ambiguous_duplicate = True

            # Smart Automatic Department Routing based on category / keyword fallback
            target_dept_id = request.POST.get('target_department')
            if target_dept_id:
                issue.department = Department.objects.filter(pk=target_dept_id).first()
            if not issue.department:
                cat = Category.objects.filter(name=issue.category).first()
                if cat and cat.department:
                    issue.department = cat.department
            if not issue.department:
                c_low = (str(issue.category) + ' ' + str(issue.title)).lower()
                if 'civil' in c_low:
                    issue.department = Department.objects.filter(name__icontains='Civil').first()
                elif any(k in c_low for k in ['lab', 'it', 'computer', 'wi-fi', 'network', 'projector', 'pc']):
                    issue.department = Department.objects.filter(Q(code='IT') | Q(name__icontains='IT')).first()
                elif any(k in c_low for k in ['electric', 'power', 'light', 'fan', 'ac', 'switch']):
                    issue.department = Department.objects.filter(Q(code='MAINT') | Q(name__icontains='Maintenance')).first()
                elif any(k in c_low for k in ['sanitat', 'washroom', 'water', 'toilet', 'clean']):
                    issue.department = Department.objects.filter(Q(code='SAN') | Q(name__icontains='Sanitation')).first()
                elif any(k in c_low for k in ['security', 'proctor', 'lock', 'guard', 'door', 'gate']):
                    issue.department = Department.objects.filter(Q(code='PROC') | Q(name__icontains='Proctor')).first()
                elif any(k in c_low for k in ['furniture', 'chair', 'desk', 'bench', 'table']):
                    issue.department = Department.objects.filter(Q(code='LOG') | Q(name__icontains='Logistics') | Q(name__icontains='Furniture')).first()
            if not issue.department:
                issue.department = Department.objects.first()

            # Backward compatibility for area
            if issue.room and not issue.area:
                area_match = Area.objects.filter(name__icontains=issue.room.floor.name).first()
                issue.area = area_match or Area.objects.first()

            # Handle multiple photo evidence attachments (maximum 3 photos)
            uploaded_photos = request.FILES.getlist('images') or request.FILES.getlist('image')
            if uploaded_photos:
                issue.image = uploaded_photos[0]

            issue.save()

            # Save additional photos (photo 2 and photo 3)
            if uploaded_photos and len(uploaded_photos) > 1:
                for extra_img in uploaded_photos[1:3]:
                    IssueImage.objects.create(issue=issue, image=extra_img)

            # Record initial history
            IssueStatusHistory.objects.create(
                issue=issue,
                previous_status='',
                new_status='submitted',
                changed_by=request.user,
                reason="Initial submission by student",
                resolution_attempt=1
            )

            # Reporter confirmation notification
            Notification.objects.create(
                user=request.user,
                notification_type='status',
                title=f"Report #{issue.id} Submitted Successfully",
                message=f"Your problem report '{issue.title}' has been received and logged in UPRS.",
                issue=issue
            )

            # Notify department staff
            if issue.department:
                staff_recipients = get_dept_staff_users(issue)
                for st in staff_recipients:
                    if st != request.user and not st.is_superuser:
                        Notification.objects.create(
                            user=st,
                            notification_type='status',
                            title=f"New Issue Assigned: #{issue.id}",
                            message=f"New report '{issue.title}' ({issue.get_priority_display()} priority) has been assigned to {issue.department.code or issue.department.name}.",
                            issue=issue
                        )

            # Central University Administrators / Superusers ALWAYS get notified of all new campus reports
            for adm in User.objects.filter(is_superuser=True):
                dept_label = f"assigned to {issue.department.name}" if issue.department else "awaiting department assignment"
                Notification.objects.create(
                    user=adm,
                    notification_type='status',
                    title=f"New Campus Issue Reported: #{issue.id}",
                    message=f"'{issue.title}' reported at {issue.get_location_display()} ({dept_label}). Priority: {issue.get_priority_display()}.",
                    issue=issue
                )

            messages.success(request, 'Campus problem reported successfully!')
            return redirect('dashboard')
    else:
        form = IssueForm()

    return render(request, 'report_problem.html', {
        'form': form,
        'buildings': Building.objects.filter(is_active=True),
        'landmarks': Landmark.objects.filter(is_active=True),
        'categories': [c[0] for c in Issue.CATEGORY_CHOICES],
        'departments': Department.objects.all().order_by('name'),
        'active_page': 'report',
    })


def issue_detail_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)

    # Privacy check
    if issue.visibility == 'private':
        if not request.user.is_authenticated or (issue.reporter != request.user and not request.user.is_staff and not request.user.is_superuser):
            messages.error(request, 'This is a private campus report and is only visible to the reporter and authorized staff.')
            return redirect('dashboard')

    # Department Isolation for Staff
    if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
        profile = getattr(request.user, 'profile', None)
        staff_dept = profile.get_effective_department() if profile else None
        if not staff_dept:
            return render(request, '403.html', {
                'title': 'No Department Assigned',
                'reason': 'Your staff account is not assigned to any operational department. Please contact the administrator.'
            }, status=403)
        if issue.department and issue.department.id != staff_dept.id and issue.reporter != request.user:
            return render(request, '403.html', {
                'title': 'Department Isolation - Access Denied',
                'reason': f'Access Denied: You are not authorized to view issues from other departments. This issue is assigned to {issue.department.name} [{issue.department.code}], while your account is assigned to {staff_dept.name} [{staff_dept.code}].'
            }, status=403)

    user_voted = False
    if request.user.is_authenticated:
        user_voted = issue.votes.filter(user=request.user).exists()

    status_history = issue.status_history.select_related('changed_by').order_by('created_at')
    comments = issue.comments.select_related('user').order_by('created_at')

    # Verifications for current resolution cycle
    verifications = issue.verifications.filter(
        resolution_attempt=issue.resolution_attempt
    ).select_related('student')
    user_verification = None
    if request.user.is_authenticated:
        user_verification = verifications.filter(student=request.user).first()

    verification_summary = issue.get_community_verification_summary()
    pending_reopen_request = issue.reopen_requests.filter(decision='pending').first()

    status_form = StatusUpdateForm(initial={'status': issue.status}) if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser) else None
    closure_form = IssueClosureForm() if request.user.is_authenticated and request.user.is_superuser else None
    verification_form = ResolutionVerificationForm() if request.user.is_authenticated else None
    reopen_form = IssueReopenForm() if request.user.is_authenticated else None

    # Similar issues on same floor/room
    similar_issues = Issue.objects.filter(
        building=issue.building
    ).exclude(pk=issue.pk).filter(status__in=['submitted', 'in_progress'])[:4]

    can_manage = can_user_manage_issue(request.user, issue) if request.user.is_authenticated else False
    is_authorized_staff = can_manage or (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
    is_dept_staff = request.user.is_authenticated and not request.user.is_superuser and (can_manage or request.user.is_staff)
    all_departments = Department.objects.all().order_by('name')

    return render(request, 'problem_detail.html', {
        'issue': issue,
        'user_voted': user_voted,
        'status_history': status_history,
        'comments': comments,
        'verifications': verifications,
        'user_verification': user_verification,
        'verification_summary': verification_summary,
        'pending_reopen_request': pending_reopen_request,
        'reopen_requests': issue.reopen_requests.all().order_by('-requested_at'),
        'status_form': status_form,
        'closure_form': closure_form,
        'verification_form': verification_form,
        'reopen_form': reopen_form,
        'similar_issues': similar_issues,
        'can_manage': can_manage,
        'is_authorized_staff': is_authorized_staff,
        'is_dept_staff': is_dept_staff,
        'all_departments': all_departments,
        'active_page': 'dashboard',
    })


@login_required
def vote_issue_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    vote = Vote.objects.filter(issue=issue, user=request.user).first()
    if vote:
        vote.delete()
        voted = False
    else:
        Vote.objects.create(issue=issue, user=request.user)
        voted = True
        if issue.reporter and issue.reporter != request.user:
            Notification.objects.create(
                user=issue.reporter,
                notification_type='vote',
                title=f"New Community Support on #{issue.id}",
                message=f"{request.user.get_full_name() or request.user.username} upvoted / supported your report '{issue.title}'.",
                issue=issue
            )

    count = issue.votes.count()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'voted': voted, 'vote_count': count})
    return redirect('problem_detail', pk=pk)


@login_required
def support_duplicate_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    _, created = Vote.objects.get_or_create(issue=issue, user=request.user)
    if created and issue.reporter and issue.reporter != request.user:
        Notification.objects.create(
            user=issue.reporter,
            notification_type='vote',
            title=f"New Support on #{issue.id}",
            message=f"{request.user.get_full_name() or request.user.username} supported your report '{issue.title}'.",
            issue=issue
        )
    messages.success(request, f'Thank you! You have supported existing report #{issue.id}: "{issue.title}".')
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def add_comment_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    content = (request.POST.get('content') or request.POST.get('text') or '').strip()
    next_url = request.POST.get('next')
    default_anchor_url = f"{reverse('problem_detail', kwargs={'pk': pk})}#comments"
    target_url = next_url if next_url else default_anchor_url

    if not content:
        messages.error(request, 'Comment cannot be empty. Please enter your remark or message.')
        return redirect(target_url)

    Comment.objects.create(
        issue=issue,
        user=request.user,
        content=content
    )

    if request.user.is_superuser:
        messages.success(request, '🛡️ Official administrative comment posted successfully.')

        # Audit log into timeline
        IssueStatusHistory.objects.create(
            issue=issue,
            previous_status=issue.status,
            new_status=issue.status,
            changed_by=request.user,
            reason=f"Official Admin Directive / Remark: {content[:150]}",
            resolution_attempt=issue.resolution_attempt
        )

        # Notify reporter
        if issue.reporter and issue.reporter != request.user:
            Notification.objects.create(
                user=issue.reporter,
                notification_type='comment',
                title=f"🛡️ Admin directive on #{issue.id}",
                message=f"University Administration commented on '{issue.title}': {content[:120]}",
                issue=issue
            )

        # Notify assigned department staff
        if issue.department:
            dept_staff_ids = UserProfile.objects.filter(assigned_department=issue.department).values_list('user_id', flat=True)
            for staff_id in dept_staff_ids:
                if staff_id != request.user.id:
                    Notification.objects.create(
                        user_id=staff_id,
                        notification_type='comment',
                        title=f"🛡️ Admin directive on #{issue.id}",
                        message=f"University Administration commented on '{issue.title}': {content[:120]}",
                        issue=issue
                    )
    else:
        role_label = "Department Staff" if request.user.is_staff else "Student"
        messages.success(request, 'Comment posted successfully.')

        # Notify reporter if comment by someone else
        if issue.reporter and issue.reporter != request.user:
            Notification.objects.create(
                user=issue.reporter,
                notification_type='comment',
                title=f"New comment on #{issue.id}",
                message=f"{request.user.get_full_name() or request.user.username} ({role_label}) commented on '{issue.title}'.",
                issue=issue
            )

        # If student commented, notify assigned department staff
        if not request.user.is_staff and issue.department:
            dept_staff_ids = UserProfile.objects.filter(assigned_department=issue.department).values_list('user_id', flat=True)
            for staff_id in dept_staff_ids:
                if staff_id != request.user.id:
                    Notification.objects.create(
                        user_id=staff_id,
                        notification_type='comment',
                        title=f"New student comment on #{issue.id}",
                        message=f"{request.user.get_full_name() or request.user.username} commented on '{issue.title}'.",
                        issue=issue
                    )

        # Notify all active administrators
        admins = User.objects.filter(is_superuser=True, is_active=True).exclude(pk=request.user.pk)
        for admin_user in admins:
            Notification.objects.create(
                user=admin_user,
                notification_type='comment',
                title=f"New comment on #{issue.id}",
                message=f"{request.user.get_full_name() or request.user.username} ({role_label}) commented on '{issue.title}'.",
                issue=issue
            )

    return redirect(target_url)


@login_required
@require_POST
def submit_resolution_verification_view(request, pk):
    """Student resolution verification."""
    issue = get_object_or_404(Issue, pk=pk)

    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Staff and administrators manage official resolutions from the management console.')
        return redirect('problem_detail', pk=pk)

    if issue.status == 'closed':
        messages.error(request, 'This issue has been closed. Please submit a Reopen Request if problem recurs.')
        return redirect('problem_detail', pk=pk)

    choice = request.POST.get('verification_choice')
    if choice not in ['appears_resolved', 'still_exists']:
        messages.error(request, 'Please select whether the problem appears resolved or still exists.')
        return redirect('problem_detail', pk=pk)

    comment = request.POST.get('comment', '').strip()
    image = request.FILES.get('image')

    verif, created = ResolutionVerification.objects.update_or_create(
        issue=issue,
        student=request.user,
        resolution_attempt=issue.resolution_attempt,
        defaults={
            'verification_choice': choice,
            'comment': comment,
            **({'image': image} if image else {}),
        }
    )

    action_str = "recorded" if created else "updated"
    messages.success(request, f'Thank you! Your resolution observation has been {action_str}.')

    # Notify staff
    staff_recipients = get_dept_staff_users(issue)
    for st in staff_recipients[:10]:
        Notification.objects.create(
            user=st,
            notification_type='verification',
            title=f'Community Verification: Issue #{issue.pk}',
            message=f'Student {request.user.get_full_name() or request.user.username} reported that "{issue.title}" {choice.replace("_", " ")}.',
            issue=issue
        )

    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def update_issue_status_view(request, pk):
    """Staff status update (submitted -> in_progress, or logging progress notes)."""
    issue = get_object_or_404(Issue, pk=pk)

    if not can_user_manage_issue(request.user, issue):
        return HttpResponseForbidden("Permission Denied: You are not authorized to update this issue.")

    new_status = request.POST.get('status')
    reason = request.POST.get('reason', '').strip()

    # STRICT WORKFLOW ENFORCEMENT:
    # 1. An issue cannot be marked 'resolved' directly via status override.
    #    The assigned department must submit an official Work Completion Report with technician, materials, and summary!
    if new_status == 'resolved':
        messages.error(
            request,
            "Workflow Enforcement: Issues cannot be directly marked as Resolved. The assigned department must complete work and submit the official Work Completion Report."
        )
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('problem_detail', pk=pk)

    # 2. An issue cannot be marked 'closed' directly via status override.
    #    It must be officially reviewed and closed by Administrators after department completion.
    if new_status == 'closed':
        messages.error(
            request,
            "Workflow Enforcement: Issues cannot be directly marked as Closed. They must be reviewed and officially closed by Administrators after department work is completed."
        )
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('problem_detail', pk=pk)

    valid_statuses = ['submitted', 'in_progress']

    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status selection.')
        return redirect('problem_detail', pk=pk)

    issue.update_status(new_status, changed_by=request.user, reason=reason)
    messages.success(request, f'Issue status updated to "{issue.get_status_display()}".')

    # Notify reporter
    if issue.reporter != request.user:
        Notification.objects.create(
            user=issue.reporter,
            notification_type='status',
            title=f'Issue Status: {issue.get_status_display()}',
            message=f'Your report "{issue.title}" has been updated to {issue.get_status_display()} by {request.user.get_full_name() or request.user.username}.',
            issue=issue
        )

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def submit_work_report_view(request, pk):
    """Department staff submits completion report with action details, technician, materials, and photo."""
    issue = get_object_or_404(Issue, pk=pk)

    if request.user.is_superuser:
        messages.error(request, "University Administrators do not submit work completion reports. Work completion reports must be submitted by the assigned department staff.")
        return redirect('problem_detail', pk=pk)

    if not can_user_manage_issue(request.user, issue):
        return HttpResponseForbidden("Permission Denied: You are not authorized to submit work reports for this issue.")

    work_summary = request.POST.get('work_report_summary', '').strip()
    technician = request.POST.get('work_technician_name', '').strip()
    materials = request.POST.get('work_materials_used', '').strip()
    image = request.FILES.get('work_completion_image')

    if not work_summary:
        messages.error(request, "Please provide a detailed work summary explaining what repairs or actions were performed.")
        return redirect('problem_detail', pk=pk)

    issue.work_report_summary = work_summary
    issue.work_technician_name = technician or (request.user.get_full_name() or request.user.username)
    issue.work_materials_used = materials
    if image:
        issue.work_completion_image = image

    issue.status = 'resolved'
    issue.resolved_by = request.user
    issue.resolved_at = timezone.now()
    issue.save()

    history_reason = f"Work Completion Report submitted: {work_summary[:100]}"
    if technician:
        history_reason += f" (Technician: {technician})"

    IssueStatusHistory.objects.create(
        issue=issue,
        previous_status='in_progress',
        new_status='resolved',
        changed_by=request.user,
        reason=history_reason,
        resolution_attempt=issue.resolution_attempt,
    )

    # Notify reporter
    if issue.reporter != request.user:
        Notification.objects.create(
            user=issue.reporter,
            notification_type='status',
            title='Department Completed Work',
            message=f'The department has submitted a work completion report for "{issue.title}".',
            issue=issue
        )

    # Notify superusers
    admin_users = User.objects.filter(is_superuser=True).exclude(id=request.user.id)
    for adm in admin_users:
        Notification.objects.create(
            user=adm,
            notification_type='status',
            title=f'Work Report Ready for Review: #{issue.id}',
            message=f'{issue.department.name if issue.department else "Department"} submitted a work completion report for "{issue.title}". Ready for admin closure.',
            issue=issue
        )

    messages.success(request, f'Work completion report submitted! Issue marked as Resolved (Awaiting final Admin review & closure).')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def request_rework_view(request, pk):
    """Admin rejects department work report and sends issue back to in_progress for rework."""
    issue = get_object_or_404(Issue, pk=pk)
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only administrators can request rework.")

    rework_reason = request.POST.get('rework_reason', '').strip() or "Admin reviewed the work report and requested additional repair or verification."
    old_status = issue.status
    issue.status = 'in_progress'
    issue.save(update_fields=['status', 'updated_at'])

    IssueStatusHistory.objects.create(
        issue=issue,
        previous_status=old_status,
        new_status='in_progress',
        changed_by=request.user,
        reason=f"Admin requested rework: {rework_reason}",
        resolution_attempt=issue.resolution_attempt,
    )

    # Notify department staff
    staff_recipients = get_dept_staff_users(issue)
    for st in staff_recipients:
        if st != request.user:
            Notification.objects.create(
                user=st,
                notification_type='status',
                title=f'Rework Requested on #{issue.id}',
                message=f'Admin requested additional work on "{issue.title}". Reason: {rework_reason}',
                issue=issue
            )

    messages.warning(request, f'Issue #{issue.id} sent back to In Progress for department rework.')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def close_issue_view(request, pk):
    """Officially close issue (superuser only, strictly after department completion)."""
    issue = get_object_or_404(Issue, pk=pk)
    if not request.user.is_superuser:
        return HttpResponseForbidden("Permission Denied: Only University Administrators can officially close campus reports.")

    # STRICT WORKFLOW ENFORCEMENT:
    # An issue can only be officially closed after the department completes work and submits a completion report (status: Resolved).
    if issue.status != 'resolved':
        messages.error(
            request,
            "Workflow Enforcement: An issue can only be officially closed after the assigned department has completed their repair work and submitted a Work Completion Report."
        )
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('problem_detail', pk=pk)

    closure_reason = request.POST.get('closure_reason', '').strip() or "Verified department completion report and officially closed."
    issue.update_status('closed', changed_by=request.user, reason=closure_reason)
    messages.success(request, f'Issue "{issue.title}" has been officially CLOSED.')

    if issue.reporter != request.user:
        Notification.objects.create(
            user=issue.reporter,
            notification_type='closure',
            title='Issue Officially Closed',
            message=f'Your report "{issue.title}" has been closed. Reason: {closure_reason}',
            issue=issue
        )

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def request_reopen_view(request, pk):
    """Student requests reopening when problem recurs."""
    issue = get_object_or_404(Issue, pk=pk)

    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Staff and administrators review reopen requests from the management console.')
        return redirect('problem_detail', pk=pk)

    if issue.status not in ['resolved', 'closed']:
        messages.error(request, 'Only resolved or closed issues can be requested for reopening.')
        return redirect('problem_detail', pk=pk)

    if issue.reopen_requests.filter(decision='pending').exists():
        messages.warning(request, 'A reopen request is already pending review for this issue.')
        return redirect('problem_detail', pk=pk)

    reopen_reason = request.POST.get('reopen_reason', '').strip()
    if not reopen_reason:
        messages.error(request, 'Please provide a reason why this problem needs to be reopened.')
        return redirect('problem_detail', pk=pk)

    reopen_req = IssueReopenRequest.objects.create(
        issue=issue,
        requester=request.user,
        reason=reopen_reason,
        requested_at=timezone.now(),
        decision='pending'
    )
    issue.reopen_requested = True
    issue.reopen_reason = reopen_reason
    issue.reopen_requested_by = request.user
    issue.reopen_requested_at = reopen_req.requested_at
    issue.save()

    messages.info(request, 'Your request to reopen this issue has been submitted for review.')

    staff_recipients = get_dept_staff_users(issue)
    for st in staff_recipients[:10]:
        Notification.objects.create(
            user=st,
            notification_type='reopen',
            title=f'Reopen Request on #{issue.pk}',
            message=f'Student {request.user.get_full_name() or request.user.username} requested to reopen "{issue.title}".',
            issue=issue
        )

    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def review_reopen_view(request, pk):
    """Staff/admin reviews reopen request."""
    issue = get_object_or_404(Issue, pk=pk)
    if not can_user_manage_issue(request.user, issue):
        return HttpResponseForbidden("Permission Denied: You are not authorized to review reopen requests for this issue.")

    action = request.POST.get('action')
    review_notes = request.POST.get('review_notes', '').strip()
    pending_req = issue.reopen_requests.filter(decision='pending').first()

    if action == 'approve':
        issue.resolution_attempt += 1
        issue.reopen_requested = False
        reason = f"Reopened by staff: {review_notes or (pending_req.reason if pending_req else issue.reopen_reason)}"
        issue.update_status('in_progress', changed_by=request.user, reason=reason, resolution_attempt=issue.resolution_attempt)

        if pending_req:
            pending_req.decision = 'approved'
            pending_req.reviewer = request.user
            pending_req.reviewed_at = timezone.now()
            pending_req.review_notes = review_notes
            pending_req.save()

        messages.success(request, f'Issue reopened. New repair cycle #{issue.resolution_attempt} started.')
    else:
        issue.reopen_requested = False
        issue.save()

        if pending_req:
            pending_req.decision = 'rejected'
            pending_req.reviewer = request.user
            pending_req.reviewed_at = timezone.now()
            pending_req.review_notes = review_notes
            pending_req.save()

        messages.info(request, 'Reopen request rejected.')

    target_user = pending_req.requester if pending_req else issue.reopen_requested_by
    if target_user:
        msg = f'Your request to reopen "{issue.title}" was {action}d.'
        Notification.objects.create(
            user=target_user,
            notification_type='reopen',
            title=f'Reopen Request {action.capitalize()}d',
            message=msg,
            issue=issue
        )

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('problem_detail', pk=pk)


@login_required
def issue_update_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.user != issue.reporter and not request.user.is_superuser:
        messages.error(request, 'Unauthorized to edit this issue.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue updated successfully.')
            return redirect('problem_detail', pk=pk)
    else:
        form = IssueForm(instance=issue)

    return render(request, 'report_problem.html', {
        'form': form,
        'buildings': Building.objects.filter(is_active=True),
        'landmarks': Landmark.objects.filter(is_active=True),
        'categories': [c[0] for c in Issue.CATEGORY_CHOICES],
        'is_edit': True,
        'active_page': 'report',
    })


@login_required
def issue_delete_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.user != issue.reporter and not request.user.is_superuser:
        messages.error(request, 'Unauthorized to delete this issue.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = issue.title
        issue.delete()
        messages.success(request, f'Issue "{title}" has been deleted.')
        return redirect('dashboard')

    return render(request, 'problem_delete.html', {'issue': issue, 'active_page': 'dashboard'})


# ==============================================================================
# 4. UNIVERSITY ADMIN PORTAL VIEWS
# ==============================================================================

@login_required
def admin_dashboard_view(request):
    """University Admin Portal Overview."""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access restricted to authorized administrators.")

    if not request.user.is_superuser:
        return redirect('department_dashboard')

    total = Issue.objects.count()
    in_progress = Issue.objects.filter(status='in_progress').count()
    resolved = Issue.objects.filter(status='resolved').count()
    closed = Issue.objects.filter(status='closed').count()
    urgent_active_count = Issue.objects.filter(priority='urgent', status__in=['submitted', 'in_progress']).count()
    high_priority = Issue.objects.annotate(v_cnt=Count('votes')).filter(
        Q(priority='high') | Q(v_cnt__gt=0),
        status__in=['submitted', 'in_progress']
    ).distinct().count()
    stats = {
        'total': total,
        'in_progress': in_progress,
        'resolved': resolved,
        'closed': closed,
        'urgent': urgent_active_count,
        'high_priority': high_priority,
    }

    pending_submitted_count = Issue.objects.filter(status='submitted').count()
    unassigned_dept_count = Issue.objects.filter(department__isnull=True).count()
    awaiting_closure_count = Issue.objects.filter(status='resolved').count()
    pending_reopens_count = IssueReopenRequest.objects.filter(decision='pending').count()
    overdue_threshold = timezone.now() - timedelta(days=3)
    overdue_count = Issue.objects.filter(status='in_progress', updated_at__lt=overdue_threshold).count()

    recent_history = IssueStatusHistory.objects.select_related('issue', 'changed_by').order_by('-created_at')[:40]
    recent_activities = []
    for h in recent_history:
        is_initial = not h.previous_status or 'initial' in (h.reason or '').lower()
        recent_activities.append({
            'timestamp': h.created_at,
            'issue': h.issue,
            'actor': h.changed_by,
            'event_type': 'status_change',
            'new_status': h.new_status,
            'new_status_display': 'Report Submitted' if is_initial else (h.get_new_status_display() if hasattr(h, 'get_new_status_display') else h.new_status.title()),
            'note': h.reason,
        })

    return render(request, 'admin/dashboard_overview.html', {
        'active_page': 'admin_dashboard',
        'admin_active': 'overview',
        'stats': stats,
        'pending_submitted_count': pending_submitted_count,
        'unassigned_dept_count': unassigned_dept_count,
        'urgent_active_count': urgent_active_count,
        'high_priority_active_count': high_priority,
        'awaiting_closure_count': awaiting_closure_count,
        'pending_reopens_count': pending_reopens_count,
        'overdue_count': overdue_count,
        'recent_activities': recent_activities,
    })


@login_required
def admin_issue_list_view(request):
    """Admin full issues table with filters."""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access restricted to authorized administrators.")

    if not request.user.is_superuser:
        return redirect('department_dashboard')

    prio_order = Case(
        When(status__in=['submitted', 'in_progress'], priority='urgent', then=Value(0)),  # Absolute Pinnacle!
        When(status__in=['submitted', 'in_progress'], priority='high', then=Value(1)),
        When(status__in=['submitted', 'in_progress'], num_votes__gt=0, then=Value(1)),
        When(status__in=['submitted', 'in_progress'], priority='medium', then=Value(2)),
        When(status__in=['submitted', 'in_progress'], priority='low', then=Value(3)),
        When(status='resolved', then=Value(4)),
        When(status='closed', then=Value(5)),
        default=Value(6),
        output_field=IntegerField()
    )

    qs = Issue.objects.all().select_related(
        'room__floor__building', 'landmark__building', 'department', 'reporter'
    ).annotate(
        num_votes=Count('votes')
    ).annotate(
        prio_rank=prio_order
    ).order_by('prio_rank', '-num_votes', '-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(room__room_number__icontains=q) |
            Q(landmark__name__icontains=q)
        )

    dept_filter = request.GET.get('department', '').strip()
    if dept_filter:
        qs = qs.filter(department_id=dept_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter == 'urgent':
        qs = qs.filter(priority='urgent')
    elif priority_filter in ['high_supported', 'urgent_high']:
        qs = qs.filter(Q(priority__in=['urgent', 'high']) | Q(num_votes__gt=0))
    elif priority_filter == 'high':
        qs = qs.filter(priority='high')
    elif priority_filter == 'supported':
        qs = qs.filter(num_votes__gt=0)
    elif priority_filter in ['medium', 'low']:
        qs = qs.filter(priority=priority_filter)

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        qs = qs.filter(category=category_filter)

    if request.GET.get('unassigned') == '1':
        qs = qs.filter(department__isnull=True)

    if request.GET.get('active') == '1':
        qs = qs.filter(status__in=['submitted', 'in_progress'])

    if request.GET.get('overdue') == '1':
        overdue_threshold = timezone.now() - timedelta(days=3)
        qs = qs.filter(status='in_progress', updated_at__lt=overdue_threshold)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all().order_by('name')
    categories = [c[0] for c in Issue.CATEGORY_CHOICES]

    return render(request, 'admin/issue_list.html', {
        'active_page': 'admin_issues',
        'admin_active': 'issues',
        'page_obj': page_obj,
        'departments': departments,
        'categories': categories,
        'query': q,
        'selected_department': dept_filter,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'selected_category': category_filter,
    })


@login_required
def admin_assign_issue_view(request):
    """Admin assigns, edits/reassigns, or revokes department assignment for an issue."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Unauthorized. Only University Administrators can assign issues.")

    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        dept_id = request.POST.get('department_id')
        action = request.POST.get('action', '')
        issue = get_object_or_404(Issue, pk=issue_id)

        if action == 'revoke' or not dept_id:
            old_dept_name = issue.department.name if issue.department else "Unassigned"
            issue.department = None
            issue.save(update_fields=['department', 'updated_at'])

            IssueStatusHistory.objects.create(
                issue=issue,
                previous_status=issue.status,
                new_status=issue.status,
                changed_by=request.user,
                reason=f"Department assignment revoked (previously assigned to {old_dept_name}) by {request.user.username}",
                resolution_attempt=issue.resolution_attempt,
            )
            messages.warning(request, f"Department assignment for Issue #{issue.id} revoked from {old_dept_name}. It is now Unassigned.")
        else:
            dept = get_object_or_404(Department, pk=dept_id)
            old_dept_name = issue.department.name if issue.department else "Unassigned"
            is_shift = (issue.department is not None and issue.department != dept)
            issue.department = dept
            issue.save(update_fields=['department', 'updated_at'])

            if is_shift:
                reason_str = f"Reassigned / Shifted to {dept.name} (previously: {old_dept_name}) by {request.user.username}"
            else:
                reason_str = f"Assigned to {dept.name} (previously: {old_dept_name}) by {request.user.username}"

            IssueStatusHistory.objects.create(
                issue=issue,
                previous_status=issue.status,
                new_status=issue.status,
                changed_by=request.user,
                reason=reason_str,
                resolution_attempt=issue.resolution_attempt,
            )

            dept_staff = UserProfile.objects.filter(assigned_department=dept).values_list('user_id', flat=True)
            for staff_uid in dept_staff:
                Notification.objects.create(
                    user_id=staff_uid,
                    title="Issue Assigned to Department",
                    message=f"Issue #{issue.id} '{issue.title}' assigned to {dept.name}.",
                    notification_type="status",
                    issue=issue
                )
            if is_shift:
                messages.success(request, f"Issue #{issue.id} department updated & shifted to {dept.name} [{dept.code}].")
            else:
                messages.success(request, f"Issue #{issue.id} assigned to {dept.name} [{dept.code}].")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'admin_departments'
    return redirect(next_url)


@login_required
def admin_change_priority_view(request, pk=None):
    """Admin Executive Control: Set or escalate issue priority to Urgent, High, Medium, or Low."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Unauthorized. Only University Administrators can modify priority directives.")

    issue_id = pk or request.POST.get('issue_id')
    issue = get_object_or_404(Issue, pk=issue_id)

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()
        new_priority = request.POST.get('priority', '').strip()
        custom_reason = request.POST.get('reason', '').strip()

        if action == 'escalate':
            target_priority = 'urgent'
        elif action == 'demote':
            target_priority = 'high'
        elif new_priority in ['urgent', 'high', 'medium', 'low']:
            target_priority = new_priority
        elif issue.priority == 'urgent':
            target_priority = 'high'
        else:
            target_priority = 'urgent'

        old_priority = issue.priority
        if old_priority != target_priority:
            issue.priority = target_priority
            issue.save(update_fields=['priority', 'updated_at'])

            old_disp = dict(Issue.PRIORITY_CHOICES).get(old_priority, old_priority.title())
            new_disp = dict(Issue.PRIORITY_CHOICES).get(target_priority, target_priority.title())
            admin_name = request.user.get_full_name() or request.user.username

            if target_priority == 'urgent':
                action_desc = f"🚨 ESCALATED TO URGENT by Admin {admin_name}"
                if custom_reason:
                    action_desc += f": {custom_reason}"
                msg = f"🚨 Issue #{issue.id} escalated to Urgent! Assigned department staff directed for emergency resolution."
            else:
                action_desc = f"Priority changed from {old_disp} to {new_disp} by Admin {admin_name}"
                if custom_reason:
                    action_desc += f": {custom_reason}"
                msg = f"Issue #{issue.id} priority updated to {new_disp}."

            IssueStatusHistory.objects.create(
                issue=issue,
                previous_status=issue.status,
                new_status=issue.status,
                changed_by=request.user,
                reason=action_desc,
                resolution_attempt=issue.resolution_attempt,
            )

            # Notify assigned department staff
            if issue.department:
                dept_staff = UserProfile.objects.filter(assigned_department=issue.department).values_list('user_id', flat=True)
                for staff_uid in dept_staff:
                    Notification.objects.create(
                        user_id=staff_uid,
                        title=f"{'🚨 Urgent Directive' if target_priority == 'urgent' else 'Priority Updated'}: Issue #{issue.id}",
                        message=f"Admin set priority to {new_disp} for Issue #{issue.id} ('{issue.title[:40]}').",
                        notification_type="status",
                        issue=issue
                    )

            messages.success(request, msg)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or redirect('problem_detail', pk=issue.pk).url
    return redirect(next_url)

admin_toggle_urgent_view = admin_change_priority_view


@login_required
def admin_resolutions_view(request):
    """Admin resolutions and student reopen requests."""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access restricted to authorized administrators.")

    if not request.user.is_superuser:
        return redirect('department_dashboard')

    pending_reopens = IssueReopenRequest.objects.filter(decision='pending').select_related(
        'issue__department', 'issue__room__floor__building', 'issue__landmark__building', 'requester'
    ).order_by('-requested_at')

    resolved_awaiting = Issue.objects.filter(status='resolved').select_related(
        'department', 'room__floor__building', 'landmark__building', 'reporter'
    ).order_by('-updated_at')

    return render(request, 'admin/resolutions_reopens.html', {
        'active_page': 'admin_resolutions',
        'admin_active': 'resolutions',
        'pending_reopens': pending_reopens,
        'resolved_awaiting': resolved_awaiting,
    })


@login_required
def admin_audit_history_view(request):
    """Audit log of all status transitions."""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access restricted to authorized administrators.")

    if not request.user.is_superuser:
        return redirect('department_dashboard')

    logs = IssueStatusHistory.objects.select_related(
        'issue__room__floor__building', 'issue__landmark__building', 'changed_by'
    ).order_by('-created_at')

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if q:
        logs = logs.filter(
            Q(issue__title__icontains=q) |
            Q(issue__id__icontains=q) |
            Q(issue__custom_location_description__icontains=q) |
            Q(issue__room__room_number__icontains=q) |
            Q(issue__floor__name__icontains=q) |
            Q(issue__building__name__icontains=q) |
            Q(changed_by__username__icontains=q) |
            Q(changed_by__first_name__icontains=q) |
            Q(changed_by__last_name__icontains=q) |
            Q(reason__icontains=q) |
            Q(new_status__icontains=q)
        )

    if status_filter and status_filter != 'all':
        logs = logs.filter(new_status=status_filter)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/audit_history.html', {
        'active_page': 'admin_audit_history',
        'admin_active': 'audit',
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
    })


# ==============================================================================
# 5. OFFLINE PWA ENDPOINTS
# ==============================================================================

def offline_sync_view(request):
    """Receive queued offline reports."""
    try:
        data = json.loads(request.body)
        items = data.get('queue', [])
        created = 0
        errors = []
        for item in items:
            loc_type = item.get('location_type', 'room')
            building = Building.objects.filter(name=item.get('building')).first() or Building.objects.first()
            room = None
            if loc_type == 'room':
                room_num = item.get('room_number', '').strip()
                room = Room.objects.filter(room_number__iexact=room_num, is_active=True).first()

            landmark = None
            if loc_type == 'landmark':
                lm_name = item.get('landmark', '').strip()
                landmark = Landmark.objects.filter(name__icontains=lm_name, is_active=True).first()

            floor = room.floor if room else None
            user = request.user if request.user.is_authenticated else User.objects.first()

            Issue.objects.create(
                title=item.get('title', 'Offline Report'),
                description=item.get('description', ''),
                category=item.get('category', 'Other'),
                location_type=loc_type,
                building=building,
                floor=floor,
                room=room,
                landmark=landmark,
                relative_position=item.get('relative_position', ''),
                custom_location_description=item.get('custom_location_description', ''),
                priority=item.get('priority', 'medium'),
                visibility=item.get('visibility', 'public'),
                reporter=user,
            )
            created += 1
        return JsonResponse({'ok': True, 'created': created, 'errors': errors})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def service_worker_view(request):
    return render(request, 'sw.js', content_type='application/javascript')


def offline_view(request):
    return render(request, 'offline.html')
