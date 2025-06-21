from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import EventForm
from .models import Event, EventJoinRequest
from django.contrib import messages
from notifications.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from geopy.distance import geodesic
from pytz import timezone as pytz_timezone
from datetime import datetime

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            # Save latitude and longitude from hidden fields
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')
            if lat:
                event.latitude = float(lat)
            if lon:
                event.longitude = float(lon)
            event.save()
            # Broadcast to all users
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "events_updates",
                {
                    "type": "event.created",
                    "event_id": event.id,
                }
            )
            return redirect('events:events_home')  # Redirect to the events home page
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})

def events_home(request):
    # Load events excluding full ones (unless user wants to see all)
    show_all = request.GET.get('show_all', False)
    
    if show_all:
        events = Event.objects.all().order_by('-created_at')
    else:
        # Exclude full events from the main view
        events = Event.objects.exclude(status='full').order_by('-created_at')
    
    # Keep track of radius preference for form display
    radius = request.GET.get('radius', '10')  # Default to 10km
    
    user_join_requests = {}
    if request.user.is_authenticated:
        for event in events:
            req = event.join_requests.filter(user=request.user).first()
            user_join_requests[event.id] = req
    
    context = {
        'events': events, 
        'user_join_requests': user_join_requests,
        'selected_radius': radius
    }
    return render(request, 'events/events.html', context)

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        event.delete()
        return redirect('events:events_home')
    return redirect('events:events_home')

@login_required
def request_join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by == request.user:
        messages.error(request, "You cannot request to join your own event.")
        return redirect('events:events_home')
    join_request, created = EventJoinRequest.objects.get_or_create(event=event, user=request.user)
    if not created:
        messages.info(request, "You have already requested to join this event.")
    else:        # Send notification to event creator
        notification = Notification.objects.create(
            user=event.created_by,
            sender=request.user,
            notification_type='event_join_request',
            message=f"{request.user.username} requested to join your event '{event.title}'.",
            url=f"/events/#event-card-{event.id}",
            related_object_id=join_request.id
        )
        # WebSocket notification
        channel_layer = get_channel_layer()
        group_name = f"notifications_{event.created_by.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "content": {
                    "message": notification.message,
                    "from_user": getattr(request.user, 'full_name', request.user.username),
                    "url": notification.url,
                    "notification_type": "event_join_request"
                }
            }
        )
        messages.success(request, "Join request sent!")
    return redirect('events:events_home')

@login_required
def handle_join_request(request, join_request_id, action):
    join_request = get_object_or_404(EventJoinRequest, id=join_request_id)
    if join_request.event.created_by != request.user:
        return HttpResponseForbidden()
    if action == 'accept':
        join_request.status = 'accepted'
        join_request.save()        # Decrement open_slots if not already 0
        event = join_request.event
        if event.open_slots > 0:
            event.open_slots -= 1
            event.save()
            # Check if event is now full and update status
            event.update_status_if_full()
        notification = Notification.objects.create(
            user=join_request.user,
            notification_type='event_join_request',
            message=f"Your request to join '{join_request.event.title}' was accepted!",
            link=f"/events/#event-card-{join_request.event.id}"
        )
        # WebSocket notification to requester
        channel_layer = get_channel_layer()
        group_name = f"notifications_{join_request.user.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "content": {
                    "message": notification.message,
                    "from_user": getattr(request.user, 'full_name', request.user.username),
                    "url": notification.link,
                    "notification_type": "event_join_request"
                }
            }
        )
    elif action == 'decline':
        join_request.status = 'declined'
        join_request.save()
        notification = Notification.objects.create(
            user=join_request.user,
            notification_type='event_join_request',
            message=f"Your request to join '{join_request.event.title}' was declined.",
            link=f"/events/#event-card-{join_request.event.id}"
        )
        # WebSocket notification to requester
        channel_layer = get_channel_layer()
        group_name = f"notifications_{join_request.user.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "content": {
                    "message": notification.message,
                    "from_user": getattr(request.user, 'full_name', request.user.username),
                    "url": notification.link,
                    "notification_type": "event_join_request"
                }
            }
        )
    return redirect('events:events_home')

@login_required
def leave_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    try:
        join_request = EventJoinRequest.objects.get(event=event, user=request.user, status='accepted')
        join_request.delete()
        event.open_slots += 1
        event.save()
        # Check if event status should change back to active
        event.update_status_if_not_full()
        messages.success(request, "You have left the event.")
    except EventJoinRequest.DoesNotExist:
        messages.error(request, "You are not a participant of this event.")
    return redirect('events:events_home')

@csrf_exempt
def quick_nearby_events(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_time = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
        user_tz = pytz_timezone(data['timezone'])
        user_lat = float(data['lat'])
        user_lng = float(data['lng'])

        quick_nearby_ids = []
        debug_info = []
        # Only consider events that are not full
        available_events = Event.objects.exclude(status='full')
        for event in available_events:
            if event.latitude is None or event.longitude is None or event.time is None:
                continue
            event_distance = geodesic((user_lat, user_lng), (event.latitude, event.longitude)).km
            event_time = event.time.astimezone(user_tz)
            seconds_until_event = (event_time - user_time).total_seconds()
            debug_info.append({
                'event_id': event.id,
                'event_title': event.title,
                'user_lat': user_lat,
                'user_lng': user_lng,
                'event_lat': event.latitude,
                'event_lng': event.longitude,
                'distance_km': event_distance,
                'seconds_until_event': seconds_until_event
            })            # Include events within 5 km and starting within the next 30 minutes (0-1800 seconds)
            if event_distance <= 5 and 0 <= seconds_until_event <= 1800:
                quick_nearby_ids.append(event.id)
        print('DEBUG quick_nearby_events:', json.dumps(debug_info, indent=2))
        return JsonResponse({'quick_nearby_ids': quick_nearby_ids, 'debug': debug_info})
