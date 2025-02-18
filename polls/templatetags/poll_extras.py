from django import template
from datetime import datetime, timezone

register = template.Library()

@register.filter
def timesince_days(value):
    """Convert timesince to days"""
    now = datetime.now(timezone.utc)
    diff = now - value
    return diff.days or 1  # Return at least 1 to avoid division by zero

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def has_voted(user_votes, poll):
    """Check if user has voted on a poll"""
    return user_votes.filter(poll=poll).exists() 