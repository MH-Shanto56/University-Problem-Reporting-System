"""
Accounts context processor.
Delegates to issues.views.notification_context to ensure 100% zero-crash operation.
"""
from issues.views import notification_context

__all__ = ['notification_context']
