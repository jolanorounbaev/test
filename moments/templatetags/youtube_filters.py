from django import template
import re

register = template.Library()

@register.filter
def youtube_id(value):
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", value)
    return match.group(1) if match else ""
