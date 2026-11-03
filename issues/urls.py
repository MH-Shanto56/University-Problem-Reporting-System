from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('report/', views.report_issue_view, name='report'),
    path('report-problem/', views.report_issue_view, name='report_problem'),

    # Problem details and actions
    path('problem/<int:pk>/', views.issue_detail_view, name='problem_detail'),
    path('problem/<int:pk>/support/', views.vote_issue_view, name='problem_support'),
    path('problem/<int:pk>/support-duplicate/', views.support_duplicate_view, name='support_duplicate'),
    path('problem/<int:pk>/update/', views.issue_update_view, name='problem_update'),
    path('problem/<int:pk>/delete/', views.issue_delete_view, name='problem_delete'),
    path('problem/<int:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('problem/<int:pk>/verify-resolution/', views.submit_resolution_verification_view, name='verify_resolution'),
    path('problem/<int:pk>/status/', views.update_issue_status_view, name='update_issue_status'),
    path('problem/<int:pk>/work-report/', views.submit_work_report_view, name='submit_work_report'),
    path('problem/<int:pk>/request-rework/', views.request_rework_view, name='request_rework'),
    path('problem/<int:pk>/close/', views.close_issue_view, name='close_issue'),
    path('problem/<int:pk>/reopen-request/', views.request_reopen_view, name='request_reopen'),
    path('problem/<int:pk>/review-reopen/', views.review_reopen_view, name='review_reopen'),
    path('problem/<int:pk>/escalate-urgent/', views.admin_change_priority_view, name='admin_toggle_urgent'),
    path('problem/<int:pk>/change-priority/', views.admin_change_priority_view, name='problem_change_priority'),

    # Backward compatibility aliases
    path('issue/<int:pk>/', views.issue_detail_view, name='issue_detail'),
    path('issue/<int:pk>/vote/', views.vote_issue_view, name='vote_issue'),
    path('issue/<int:pk>/update/', views.issue_update_view, name='issue_update'),
    path('issue/<int:pk>/delete/', views.issue_delete_view, name='issue_delete'),

    # Admin Portal
    path('admin-portal/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-portal/issues/', views.admin_issue_list_view, name='admin_issues'),
    path('admin-portal/assign-issue/', views.admin_assign_issue_view, name='admin_assign_issue'),
    path('admin-portal/change-priority/', views.admin_change_priority_view, name='admin_change_priority'),
    path('admin-portal/resolutions/', views.admin_resolutions_view, name='admin_resolutions'),
    path('admin-portal/audit-history/', views.admin_audit_history_view, name='admin_audit_history'),

    # Offline PWA
    path('api/offline-sync/', views.offline_sync_view, name='offline_sync'),
    path('sw.js', views.service_worker_view, name='sw'),
    path('offline/', views.offline_view, name='offline'),
]
