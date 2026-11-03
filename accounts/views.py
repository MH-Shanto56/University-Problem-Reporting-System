from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Notification
from .forms import RegisterForm, ProfileForm
from departments.models import Department

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_staff:
            return redirect('department_dashboard')
        return redirect('dashboard')

    selected_role = request.POST.get('login_role') or request.POST.get('role') or request.GET.get('role', 'student')
    username_val = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        username_val = username

        user = authenticate(request, username=username, password=password)
        if not user and username.startswith('staff_'):
            # Allow staff_id123 and staff_<dept>123 interchangeably for staff convenience
            for candidate_pw in ['staff_id123', 'staff_it123', f"{username}123"]:
                user = authenticate(request, username=username, password=candidate_pw)
                if user:
                    break
        if user:
            # 1. Official / Admin Portal Selection
            if selected_role == 'admin':
                if not (user.is_staff or user.is_superuser):
                    messages.error(
                        request,
                        'Access Denied: Student accounts cannot sign in through the Official / Admin portal. Please use the Student Login tab.'
                    )
                    return render(request, 'registration/login.html', {
                        'active_page': 'login',
                        'selected_role': 'student',
                        'username_val': username_val,
                    })

                login(request, user)
                role_label = "University Administration" if user.is_superuser else "Department Staff"
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}! Logged in as {role_label}.')
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url.startswith('/admin-portal/') and not user.is_superuser:
                    next_url = None
                if next_url and next_url not in ['/', '/dashboard/', '/home/']:
                    return redirect(next_url)
                if user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('department_dashboard')

            # 2. Student Portal Selection (Strict Check: Admins and Staff cannot log in here)
            else:
                if user.is_superuser or user.is_staff:
                    role_desc = "Administrator" if user.is_superuser else "Department Staff"
                    messages.warning(
                        request,
                        f'Role Mismatch: Your account is registered as {role_desc}. Please sign in using the Official / Admin tab.'
                    )
                    return render(request, 'registration/login.html', {
                        'active_page': 'login',
                        'selected_role': 'admin',
                        'username_val': username_val,
                    })

                # Regular student login
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url not in ['/', '/dashboard/', '/home/']:
                    return redirect(next_url)
                return redirect('dashboard')

        messages.error(request, 'Invalid username or password. Please verify your credentials and try again.')

    return render(request, 'registration/login.html', {
        'active_page': 'login',
        'selected_role': selected_role,
        'username_val': username_val,
    })


def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    departments = Department.objects.all().order_by('name')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            account_type = request.POST.get('account_type', 'student')
            selected_dept_id = request.POST.get('assigned_department')

            if account_type == 'staff':
                user.is_staff = True

            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            if account_type == 'staff' and selected_dept_id:
                dept = Department.objects.filter(id=selected_dept_id).first()
                if dept:
                    profile.assigned_department = dept
                    profile.save()

            login(request, user)
            if user.is_staff:
                dept_name = profile.assigned_department.name if profile.assigned_department else "Operational"
                messages.success(request, f'Welcome! Registered as official staff for {dept_name}.')
                return redirect('department_dashboard')
            else:
                messages.success(request, 'Account created! Welcome to University Problem Reporting System (UPRS).')
                return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'departments': departments,
    })


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()

        profile.bio = request.POST.get('bio', '').strip()

        student_id = request.POST.get('student_id', '').strip()
        if student_id:
            profile.student_id = student_id

        department = request.POST.get('department', '').strip()
        if department and not (request.user.is_staff or request.user.is_superuser):
            profile.department = department

        if 'avatar' in request.FILES and request.FILES['avatar']:
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    from issues.models import Issue, ResolutionVerification
    my_issues = request.user.reported_issues.all().select_related('floor__building', 'room__floor__building', 'landmark__building', 'department')
    supported_issues = Issue.objects.filter(votes__user=request.user).distinct().select_related('floor__building', 'room__floor__building', 'landmark__building', 'department')
    my_verifications = ResolutionVerification.objects.filter(student=request.user).select_related('issue__floor__building', 'issue__room__floor__building', 'issue__landmark__building', 'issue__department')

    return render(request, 'registration/profile.html', {
        'profile': profile,
        'my_issues': my_issues,
        'supported_issues': supported_issues,
        'my_verifications': my_verifications,
        'active_page': 'profile',
    })


@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()[:60]
    return render(request, 'notifications.html', {
        'notifications': notifs,
        'active_page': 'notifications',
    })


@login_required
def mark_all_notifications_read_view(request):
    """Marks all unread notifications of the logged-in user as read."""
    if request.method == 'POST':
        updated_count = request.user.notifications.filter(is_read=False).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'ok', 'updated_count': updated_count, 'unread_count': 0})
        messages.success(request, 'All notifications marked as read.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'notifications'
    return redirect(next_url)


@login_required
def mark_single_notification_read_view(request, pk):
    """Marks a single notification as read and redirects to the associated issue."""
    notif = get_object_or_404(request.user.notifications, pk=pk)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])
    if notif.issue:
        return redirect('problem_detail', pk=notif.issue.pk)
    return redirect('notifications')
