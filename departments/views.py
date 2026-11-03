import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.contrib.auth.models import User
from .models import Department

def get_user_dept(user):
    """Simple helper to get assigned department of staff."""
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, 'profile', None)
    if profile:
        return profile.get_effective_department()
    return None


@login_required
def department_dashboard_view(request):
    """Dynamic Department Staff Dashboard."""
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, '403.html', {
            'title': 'Staff Access Required',
            'reason': 'The Department Staff Dashboard is restricted to authorized university department personnel and administrators. You are currently logged in with a student account.'
        }, status=403)

    dept = None
    all_departments = None
    selected_dept_id = request.GET.get('dept', '')

    if not request.user.is_superuser:
        dept = get_user_dept(request.user)
        if not dept:
            return render(request, '403.html', {
                'title': 'Access Denied: No Department Assigned',
                'reason': 'Access Denied: Your staff account has not been assigned to an operational university department yet. Please contact the University Administrator.'
            }, status=403)
    else:
        all_departments = Department.objects.all().order_by('name')
        if selected_dept_id and selected_dept_id != 'all':
            dept = Department.objects.filter(id=selected_dept_id).first()

    from issues.models import Issue
    base_qs = Issue.objects.all().select_related(
        'room__floor__building', 'landmark__building', 'floor__building', 'department', 'reporter'
    )
    if dept:
        base_qs = base_qs.filter(department=dept)

    from locations.models import Building

    stat_new_assigned = base_qs.filter(status='submitted').count()
    stat_in_progress = base_qs.filter(status='in_progress').count()
    stat_resolved = base_qs.filter(status='resolved').count()
    stat_urgent = base_qs.filter(priority='urgent', status__in=['submitted', 'in_progress']).count()
    stat_high_priority = base_qs.annotate(v_cnt=Count('votes')).filter(
        Q(priority='high') | Q(v_cnt__gt=0),
        status__in=['submitted', 'in_progress']
    ).distinct().count()
    stat_closed = base_qs.filter(status='closed').count()
    stat_total_assigned = base_qs.count()

    resolved_closed = stat_resolved + stat_closed
    resolution_rate = round((resolved_closed / stat_total_assigned) * 100, 1) if stat_total_assigned > 0 else 0.0
    resolution_rate_display = f"{resolution_rate}%" if stat_total_assigned > 0 else "N/A"

    pending_reopen_count = base_qs.filter(
        Q(reopen_requests__decision='pending') | Q(reopen_requested=True)
    ).distinct().count()

    # Filter parameters
    status_filter = request.GET.get('status', 'all').strip()
    priority_filter = request.GET.get('priority', 'all').strip()
    category_filter = request.GET.get('category', 'all').strip()
    building_filter = request.GET.get('building', 'all').strip()
    sort_by = request.GET.get('sort', 'priority_first').strip()
    search_query = request.GET.get('q', '').strip()

    filtered_qs = base_qs

    # Status filter
    if status_filter in ['new', 'submitted']:
        filtered_qs = filtered_qs.filter(status='submitted')
    elif status_filter == 'in_progress':
        filtered_qs = filtered_qs.filter(status='in_progress')
    elif status_filter == 'resolved':
        filtered_qs = filtered_qs.filter(status='resolved')
    elif status_filter == 'closed':
        filtered_qs = filtered_qs.filter(status='closed')
    elif status_filter == 'high_priority':
        filtered_qs = filtered_qs.annotate(v_filter_cnt=Count('votes')).filter(
            (Q(priority__in=['high', 'urgent']) | Q(v_filter_cnt__gt=0)) & Q(status__in=['submitted', 'in_progress'])
        )
    elif status_filter == 'reopen':
        filtered_qs = filtered_qs.filter(
            Q(reopen_requests__decision='pending') | Q(reopen_requested=True)
        ).distinct()

    # Priority filter (Urgent, High, Medium, Low + Parallel Community Support)
    if priority_filter == 'urgent':
        filtered_qs = filtered_qs.filter(priority='urgent')
    elif priority_filter in ['high_supported', 'urgent_high']:
        filtered_qs = filtered_qs.annotate(v_filter_cnt=Count('votes')).filter(
            Q(priority__in=['high', 'urgent']) | Q(v_filter_cnt__gt=0)
        )
    elif priority_filter == 'high':
        filtered_qs = filtered_qs.filter(priority='high')
    elif priority_filter == 'supported':
        filtered_qs = filtered_qs.annotate(v_filter_cnt=Count('votes')).filter(v_filter_cnt__gt=0)
    elif priority_filter in ['medium', 'low']:
        filtered_qs = filtered_qs.filter(priority=priority_filter)

    # Category filter
    if category_filter and category_filter != 'all':
        filtered_qs = filtered_qs.filter(category=category_filter)

    # Building filter
    if building_filter and building_filter != 'all':
        filtered_qs = filtered_qs.filter(building_id=building_filter)

    # Comprehensive multi-field and ID search
    if search_query:
        clean_id_candidate = search_query.lstrip('#').strip()
        search_filter = (
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(room__room_number__icontains=search_query) |
            Q(room__name__icontains=search_query) |
            Q(floor__name__icontains=search_query) |
            Q(building__name__icontains=search_query) |
            Q(landmark__name__icontains=search_query) |
            Q(reporter__username__icontains=search_query) |
            Q(reporter__first_name__icontains=search_query) |
            Q(reporter__last_name__icontains=search_query) |
            Q(work_technician_name__icontains=search_query)
        )
        if clean_id_candidate.isdigit():
            search_filter = search_filter | Q(id=int(clean_id_candidate))
        filtered_qs = filtered_qs.filter(search_filter)

    from django.core.paginator import Paginator

    # Admin Urgent Escalation + Parallel Community Support Ranking:
    # Rank 0: URGENT (Admin Escalated) -> Absolute Pinnacle Priority!
    # Rank 1: Active issues that are High Priority OR have Community Support (votes > 0)
    # Rank 2: Active Medium Priority (0 votes)
    # Rank 3: Active Low Priority (0 votes)
    # Rank 4: Resolved issues
    # Rank 5: Closed issues
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

    # Status order: Active (submitted 1, in_progress 2), Resolved (3), Closed (4)
    status_order = Case(
        When(status='submitted', then=Value(1)),
        When(status='in_progress', then=Value(2)),
        When(status='resolved', then=Value(3)),
        When(status='closed', then=Value(4)),
        default=Value(5),
        output_field=IntegerField()
    )

    annotated_qs = filtered_qs.prefetch_related('status_history', 'reopen_requests').annotate(
        num_votes=Count('votes')
    ).annotate(
        prio_rank=prio_order,
        status_rank=status_order
    )

    # Sorting options
    if sort_by == 'newest':
        issues_qs = annotated_qs.order_by('-created_at')
    elif sort_by == 'oldest':
        issues_qs = annotated_qs.order_by('created_at')
    elif sort_by == 'status':
        issues_qs = annotated_qs.order_by('status_rank', 'prio_rank', '-num_votes', '-created_at')
    elif sort_by == 'votes':
        issues_qs = annotated_qs.order_by('-num_votes', 'prio_rank', '-created_at')
    elif sort_by == 'id_desc':
        issues_qs = annotated_qs.order_by('-id')
    elif sort_by == 'id_asc':
        issues_qs = annotated_qs.order_by('id')
    else:
        # Default: High Priority & Community Supported at the very top (sorted by most votes first)!
        issues_qs = annotated_qs.order_by('prio_rank', '-num_votes', 'status_rank', '-created_at')

    filtered_count = filtered_qs.count()
    paginator = Paginator(issues_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    has_active_filters = bool(
        search_query or
        (priority_filter and priority_filter != 'all') or
        (category_filter and category_filter != 'all') or
        (building_filter and building_filter != 'all') or
        (status_filter and status_filter != 'all') or
        (sort_by and sort_by != 'priority_first')
    )

    all_buildings = Building.objects.all().order_by('name')
    category_choices = Issue.CATEGORY_CHOICES

    return render(request, 'department_dashboard.html', {
        'department': dept,
        'all_departments': all_departments,
        'selected_dept_id': selected_dept_id,
        'stat_new_assigned': stat_new_assigned,
        'stat_in_progress': stat_in_progress,
        'stat_resolved': stat_resolved,
        'stat_urgent': stat_urgent,
        'stat_high_priority': stat_high_priority,
        'stat_closed': stat_closed,
        'stat_total_assigned': stat_total_assigned,
        'stat_active_workload': stat_new_assigned + stat_in_progress,
        'resolution_rate': resolution_rate,
        'resolution_rate_display': resolution_rate_display,
        'pending_reopen_count': pending_reopen_count,
        'reopen_count': pending_reopen_count,
        'issues': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'filter_status': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'building_filter': building_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'has_active_filters': has_active_filters,
        'filtered_count': filtered_count,
        'all_buildings': all_buildings,
        'category_choices': category_choices,
        'active_page': 'department_dashboard',
    })


@login_required
def department_performance_view(request):
    """Department Performance Board - Restricted to University Administrators."""
    if not request.user.is_superuser:
        messages.info(request, 'The campus-wide department performance board is restricted to University Administrators.')
        return redirect('department_dashboard')

    from issues.models import Issue
    departments = Department.objects.all().order_by('name')
    dept_stats = []

    for dept in departments:
        dept_issues = Issue.objects.filter(department=dept)
        total_assigned = dept_issues.count()
        resolved_count = dept_issues.filter(status='resolved').count()
        closed_count = dept_issues.filter(status='closed').count()
        resolved_closed = resolved_count + closed_count

        rate = round((resolved_closed / total_assigned) * 100, 1) if total_assigned > 0 else 0.0
        rate_display = f"{rate}%" if total_assigned > 0 else "N/A"

        in_progress_count = dept_issues.filter(status='in_progress').count()
        submitted_count = dept_issues.filter(status='submitted').count()
        active_count = in_progress_count + submitted_count

        stat_item = {
            'department': dept,
            'name': dept.name,
            'code': dept.code,
            'head_name': "Department Supervisor",
            'contact_email': dept.contact_email or "uprs-support@uap-bd.edu",
            'total_assigned': total_assigned,
            'in_progress_count': in_progress_count,
            'submitted_count': submitted_count,
            'active_count': active_count,
            'resolved_count': resolved_count,
            'closed_count': closed_count,
            'resolved_closed': resolved_closed,
            'resolution_rate': rate,
            'resolution_rate_display': rate_display,
            'avg_resolution_time': "N/A",
            'staff_count': dept.staff_profiles.count(),
            'overdue_count': '0',
        }
        dept_stats.append(stat_item)

    total_assigned_all = sum(s['total_assigned'] for s in dept_stats)
    total_resolved_all = sum(s['resolved_closed'] for s in dept_stats)
    total_active_all = sum(s['active_count'] for s in dept_stats)
    overall_resolution_rate = round((total_resolved_all / total_assigned_all * 100), 1) if total_assigned_all > 0 else 0

    top_dept = None
    eligible = [s for s in dept_stats if s['total_assigned'] > 0]
    if eligible:
        top_dept = max(eligible, key=lambda x: (x['resolution_rate'], x['resolved_closed']))

    summary_stats = {
        'total_assigned': total_assigned_all,
        'total_resolved': total_resolved_all,
        'total_active': total_active_all,
        'overall_rate': overall_resolution_rate,
        'top_department': top_dept,
        'top_dept': top_dept,
    }

    chart_data = {
        'labels': [s['code'] for s in dept_stats],
        'names': [s['name'] for s in dept_stats],
        'assigned': [s['total_assigned'] for s in dept_stats],
        'resolved': [s['resolved_closed'] for s in dept_stats],
        'active': [s['in_progress_count'] for s in dept_stats],
        'rates': [s['resolution_rate'] for s in dept_stats],
    }
    perf_chart_json = json.dumps(chart_data)

    template_name = 'admin/department_performance.html' if (request.user.is_authenticated and request.user.is_superuser) else 'department_performance.html'
    return render(request, template_name, {
        'departments': departments,
        'dept_stats': dept_stats,
        'summary': summary_stats,
        'summary_stats': summary_stats,
        'perf_chart_json': perf_chart_json,
        'active_page': 'department_performance',
    })


@login_required
def admin_departments_view(request):
    """Admin Portal: Departments management & staff reassignment."""
    if not request.user.is_superuser:
        return render(request, '403.html', {'reason': 'Access restricted to University Administrators.'}, status=403)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_department':
            dept_name = request.POST.get('name', '').strip()
            dept_code = request.POST.get('code', '').strip().upper()
            dept_email = request.POST.get('contact_email', '').strip()
            dept_desc = request.POST.get('description', '').strip()

            if not dept_name or not dept_code:
                messages.error(request, "Department Name and Code are required.")
            elif Department.objects.filter(Q(name__iexact=dept_name) | Q(code__iexact=dept_code)).exists():
                messages.error(request, f"Department '{dept_name}' or code '{dept_code}' already exists.")
            else:
                new_dept = Department.objects.create(
                    name=dept_name, code=dept_code, contact_email=dept_email, description=dept_desc
                )
                messages.success(request, f"New Department '{new_dept.name} [{new_dept.code}]' created successfully!")
            return redirect('admin_departments')

        elif action == 'edit_department':
            dept_id = request.POST.get('department_id')
            target_dept = get_object_or_404(Department, id=dept_id)
            dept_name = request.POST.get('name', '').strip()
            dept_code = request.POST.get('code', '').strip().upper()
            dept_email = request.POST.get('contact_email', '').strip()
            dept_desc = request.POST.get('description', '').strip()

            if not dept_name or not dept_code:
                messages.error(request, "Department Name and Short Code are required.")
            elif Department.objects.filter(~Q(id=target_dept.id) & (Q(name__iexact=dept_name) | Q(code__iexact=dept_code))).exists():
                messages.error(request, f"Another department with name '{dept_name}' or code '{dept_code}' already exists.")
            else:
                old_code = target_dept.code
                target_dept.name = dept_name
                target_dept.code = dept_code
                target_dept.contact_email = dept_email
                target_dept.description = dept_desc
                target_dept.save()

                if old_code != dept_code:
                    from accounts.models import UserProfile
                    UserProfile.objects.filter(assigned_department=target_dept).update(department=dept_code)

                messages.success(request, f"Department '{target_dept.name} [{target_dept.code}]' updated successfully!")
            return redirect('admin_departments')

        elif action == 'delete_department':
            dept_id = request.POST.get('department_id')
            target_dept = get_object_or_404(Department, id=dept_id)
            dept_name = target_dept.name
            dept_code = target_dept.code
            target_dept.delete()
            messages.success(request, f"Department '{dept_name} [{dept_code}]' deleted successfully. Related issues and staff are now unassigned.")
            return redirect('admin_departments')

        elif action == 'create_staff':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            dept_id = request.POST.get('assigned_department_id')
            role = request.POST.get('role', 'staff')

            if not username or not password:
                messages.error(request, "User ID (Username) and Password are required to create a staff account.")
            elif User.objects.filter(username__iexact=username).exists():
                messages.error(request, f"User ID '{username}' already exists. Please choose a different username.")
            else:
                first_name = full_name.split()[0] if full_name else ''
                last_name = ' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ''
                new_user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.is_staff = True
                if role == 'superuser':
                    new_user.is_superuser = True
                new_user.save()

                dept = Department.objects.filter(id=dept_id).first() if dept_id else None
                from accounts.models import UserProfile
                UserProfile.objects.create(
                    user=new_user,
                    department=dept.code if dept else 'STAFF',
                    assigned_department=dept
                )
                dept_name = dept.name if dept else "Global / Unassigned"
                messages.success(request, f"Staff account '{username}' created successfully for {dept_name}! Login Password set.")
            return redirect('admin_departments')

        elif action == 'edit_staff':
            user_id = request.POST.get('user_id')
            target_user = get_object_or_404(User, id=user_id)
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            dept_id = request.POST.get('assigned_department_id')
            new_password = request.POST.get('new_password', '').strip()
            role = request.POST.get('role', 'staff')
            is_active = request.POST.get('is_active') in ['on', 'true', '1']

            if full_name:
                target_user.first_name = full_name.split()[0]
                target_user.last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            target_user.email = email
            target_user.is_active = is_active

            # Prevent removing superuser from oneself accidentally
            if target_user.id != request.user.id:
                if role == 'superuser':
                    target_user.is_superuser = True
                    target_user.is_staff = True
                else:
                    target_user.is_superuser = False
                    target_user.is_staff = True

            if new_password:
                target_user.set_password(new_password)
                messages.info(request, f"Password updated for staff account '{target_user.username}'.")

            target_user.save()

            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=target_user)
            dept = Department.objects.filter(id=dept_id).first() if dept_id else None
            profile.assigned_department = dept
            if dept:
                profile.department = dept.code
            profile.save()

            messages.success(request, f"Staff account '{target_user.username}' updated successfully.")
            return redirect('admin_departments')

        elif action == 'delete_staff':
            user_id = request.POST.get('user_id')
            target_user = get_object_or_404(User, id=user_id)
            if target_user.id == request.user.id:
                messages.error(request, "You cannot delete your own logged-in administrator account.")
            elif target_user.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
                messages.error(request, "Cannot delete the sole superuser of the system.")
            else:
                uname = target_user.username
                target_user.delete()
                messages.success(request, f"Staff account '{uname}' deleted successfully.")
            return redirect('admin_departments')

        user_id = request.POST.get('user_id')
        dept_id = request.POST.get('assigned_department_id')
        if user_id:
            from accounts.models import UserProfile
            target_user = get_object_or_404(User, id=user_id)
            profile, _ = UserProfile.objects.get_or_create(user=target_user)
            if dept_id:
                dept = get_object_or_404(Department, id=dept_id)
                profile.assigned_department = dept
                profile.save()
                messages.success(request, f"Successfully assigned {target_user.username} to {dept.name}.")
            else:
                profile.assigned_department = None
                profile.save()
                messages.success(request, f"Department assignment revoked for {target_user.username}.")
        return redirect('admin_departments')

    from issues.models import Issue
    departments = Department.objects.prefetch_related('staff_profiles', 'issues').order_by('name')
    staff_members = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).select_related('profile__assigned_department').order_by('username')
    active_issues = Issue.objects.filter(status__in=['submitted', 'in_progress']).select_related('department', 'room__floor__building', 'landmark__building', 'reporter').order_by('-created_at')[:30]

    return render(request, 'admin/departments_staff.html', {
        'active_page': 'admin_departments',
        'admin_active': 'departments',
        'departments': departments,
        'staff_members': staff_members,
        'active_issues': active_issues,
    })
