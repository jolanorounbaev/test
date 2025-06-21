from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter  
def default_if_none(value, default):
    """Return default if value is None"""
    return default if value is None else value

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract the argument from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0
