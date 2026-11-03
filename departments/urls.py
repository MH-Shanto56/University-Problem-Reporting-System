from django.urls import path
from . import views

urlpatterns = [
    path('department/dashboard/', views.department_dashboard_view, name='department_dashboard'),
    path('performance/', views.department_performance_view, name='department_performance'),
    path('leaderboard/', views.department_performance_view, name='leaderboard'),
    path('admin-portal/departments/', views.admin_departments_view, name='admin_departments'),
]
