from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import FriendRequest, Notification
from django.contrib.auth import get_user_model
from django.apps import apps
from django.http import JsonResponse

User = get_user_model()
Friendship = apps.get_model('notifications', 'Friendship')

def base_context(request):
    if request.user.is_authenticated:
        friend_request_count = FriendRequest.objects.filter(to_user=request.user, accepted=False, declined=False).count()
    else:
        friend_request_count = 0
    return {'friend_request_count': friend_request_count}

@login_required
def notifications_dropdown(request):
    requests = FriendRequest.objects.filter(to_user=request.user, accepted=False, declined=False).order_by('-timestamp')
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')[:20]
    return render(request, 'notifications/notifications_dropdown.html', {
        'requests': requests,
        'notifications': notifications
    })

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.accepted = True
    friend_request.save()

    # Create a Friendship (both directions)
    Friendship.objects.get_or_create(user1=friend_request.from_user, user2=friend_request.to_user)
    Friendship.objects.get_or_create(user1=friend_request.to_user, user2=friend_request.from_user)

    # TODO: Optionally, create a notification for the sender that their request was accepted

    return redirect(request.META.get('HTTP_REFERER', 'notifications:notifications_dropdown'))

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.declined = True
    friend_request.save()
    return redirect(request.META.get('HTTP_REFERER', 'notifications:notifications_dropdown'))

@login_required
def unread_count(request):
    count = FriendRequest.objects.filter(to_user=request.user, accepted=False, declined=False).count()
    return JsonResponse({'count': count})
