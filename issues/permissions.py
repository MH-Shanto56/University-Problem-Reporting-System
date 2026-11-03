"""
Issues app permissions module.
Delegates to issues.views permissions.
"""
from issues.views import (
    get_user_department,
    user_can_manage_issue,
    can_user_manage_issue,
    get_department_staff_recipients,
    get_dept_staff_users,
)

__all__ = [
    'get_user_department',
    'user_can_manage_issue',
    'can_user_manage_issue',
    'get_department_staff_recipients',
    'get_dept_staff_users',
]
