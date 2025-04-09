from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notifications_dropdown(request):
    notifications = Notification.objects.filter(to_user=request.user, is_read=False)[:10]
    return render(request, 'notifications/notifications_dropdown.html', {
        'notifications': notifications
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FriendRequest, Notification
from django.conf import settings

@login_required
def send_friend_request(request, user_id):
    if request.method == 'POST':
        from_user = request.user
        to_user = get_object_or_404(settings.AUTH_USER_MODEL, id=user_id)
        
        # Check if request already exists
        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
            messages.warning(request, 'Friend request already sent')
        else:
            friend_request = FriendRequest.objects.create(
                from_user=from_user,
                to_user=to_user
            )
            # Create notification
            Notification.create_friend_request_notification(from_user, to_user)
            messages.success(request, 'Friend request sent')
        
        return redirect('profile', user_id=user_id)
    return redirect('home')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.accept()
    messages.success(request, 'Friend request accepted')
    return redirect('friend_requests')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.reject()
    messages.success(request, 'Friend request declined')
    return redirect('friend_requests')

@login_required
def friend_requests(request):
    received_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(from_user=request.user, status='pending')
    return render(request, 'notifications/friend_requests.html', {
        'received_requests': received_requests,
        'sent_requests': sent_requests
    })


from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, to_user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def unread_count(request):
    count = Notification.objects.filter(to_user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@require_POST
@login_required
def mark_as_seen(request):
    # Mark notifications as "seen" (but not necessarily read)
    # You might want to implement this differently
    request.user.notifications.filter(is_read=False).update(is_seen=True)
    return JsonResponse({'success': True})
