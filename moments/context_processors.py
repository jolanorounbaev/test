from .models import Moment
from django.utils import timezone
from datetime import timedelta

def on_fire_moments_processor(request):
    """
    Context processor to provide on fire moments globally
    """
    try:
        # Get moments that are "on fire" (high fire count and recent)
        on_fire_moments = Moment.objects.filter(
            is_active=True,
            fire_count__gte=5,  # At least 5 fire reactions
            created_at__gte=timezone.now() - timedelta(hours=24)  # Within last 24 hours
        ).order_by('-fire_count', '-created_at')[:5]  # Top 5 moments
        
        return {
            'on_fire_moments': on_fire_moments
        }
    except:
        # If there's any error, return empty
        return {
            'on_fire_moments': []
        }
