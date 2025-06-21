from celery import shared_task
from django.utils import timezone
from .models import Moment
from datetime import timedelta

@shared_task
def expire_old_moments():
    Moment.objects.filter(expires_at__lte=timezone.now(), is_active=True).update(is_active=False)

@shared_task
def decay_moment_activity():
    threshold = timezone.now() - timedelta(minutes=5)
    Moment.objects.filter(last_active__lt=threshold).update(activity_count=0)

from celery import shared_task

@shared_task
def test_hello():
    print("✅ Hello from Celery!")
    return "Hello, world!"
