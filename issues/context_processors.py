"""
Issues app context processor module.
Delegates to issues.views.notification_context.
"""
from issues.views import notification_context

__all__ = ['notification_context']
