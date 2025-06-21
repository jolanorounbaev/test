from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatRoom, Message
from registerandlogin.models import CustomUser
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from notifications.models import get_friends
from userprofile.models import Block
from django.db import models
import json
import datetime
from django.utils import timezone

def is_user_blocked(current_user, other_user):
    """Check if users have blocked each other"""
    return Block.objects.filter(
        models.Q(blocker=current_user, blocked=other_user) | 
        models.Q(blocker=other_user, blocked=current_user)
    ).exists()

@login_required
def chat_home(request, room_id=None):
    rooms = ChatRoom.objects.filter(participants=request.user).prefetch_related('participants', 'messages')
    
    # Clean up orphaned rooms (where the other participant was deleted)
    orphaned_rooms = []
    for room in rooms:
        if not room.is_group:
            other_participants = room.participants.exclude(id=request.user.id)
            if other_participants.count() == 0:
                # No other participants exist, this room should be deleted
                orphaned_rooms.append(room)
    
    # Delete orphaned rooms
    for room in orphaned_rooms:
        room.delete()
    
    # Refresh the rooms list after cleanup
    rooms = ChatRoom.objects.filter(participants=request.user).prefetch_related('participants', 'messages')

    # If a chat is opened, remember it in the session
    if room_id:
        request.session['last_chat_room_id'] = room_id
    
    # If no room_id, try to restore last opened chat from session
    if not room_id:
        last_chat_room_id = request.session.get('last_chat_room_id')
        if last_chat_room_id:
            # Validate the room exists and user is a participant
            try:
                last_room = ChatRoom.objects.get(id=last_chat_room_id, participants=request.user)
                return redirect('chat_room', room_id=last_room.id)
            except ChatRoom.DoesNotExist:
                pass  # Fallback to most recent chat if not found
        if rooms.exists():
            # Find the most recent chat (by last message timestamp, fallback to room id)
            def last_msg_time(room):
                last_msg = room.messages.order_by('-timestamp').first()
                if last_msg:
                    return last_msg.timestamp
                return timezone.make_aware(datetime.datetime.min.replace(year=1970))
            most_recent_room = max(rooms, key=last_msg_time)
            return redirect('chat_room', room_id=most_recent_room.id)

    for room in rooms:
        if not room.is_group:            # Fetch the full user object for other_participant
            other = room.participants.exclude(id=request.user.id).first()
            if other:
                user_obj = CustomUser.objects.get(id=other.id)
                print("DEBUG sidebar other_participant:", user_obj.email, user_obj.profile_picture)
                room.other_participant = user_obj
            else:
                room.other_participant = None
        room.last_message = room.messages.order_by('-timestamp').first()
        if room.last_message:
            room.last_message.is_blocked = is_user_blocked(request.user, room.last_message.sender)
        room.unread_count = room.messages.exclude(sender__id=request.user.id).filter(read=False).count()

    active_room = None
    chat_messages = []
    chat_partner = None

    if room_id:
        active_room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
        chat_messages = active_room.messages.select_related('sender').order_by('timestamp')[:50]
        
        # Add blocking info to messages
        for message in chat_messages:
            message.is_blocked = is_user_blocked(request.user, message.sender)
        
        active_room.messages.exclude(sender__id=request.user.id).update(read=True)  # Mark as read

        if not active_room.is_group:
            other = active_room.participants.exclude(id=request.user.id).first()
            if other:
                user_obj = CustomUser.objects.get(id=other.id)
                print("DEBUG active_room other_participant:", user_obj.email, user_obj.profile_picture)
                active_room.other_participant = user_obj
                chat_partner = active_room.other_participant  # ✅ Pass this to template
            else:
                active_room.other_participant = None
                chat_partner = None
    else:
        chat_messages = []

    # Provide only friends for group chat creation
    all_users = get_friends(request.user)

    return render(request, 'chat/chat.html', {
        'chat_rooms': rooms,
        'active_room': active_room,
        'chat_messages': chat_messages,
        'user': request.user,
        'chat_partner': chat_partner,
        'all_users': all_users,  # For group chat creation modal
    })




@csrf_exempt  # only needed if not using CSRF in frontend; remove if you use {% csrf_token %}
def send_message(request, room_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    message_text = request.POST.get('message', '').strip()
    image_file = request.FILES.get('image')
    video_file = request.FILES.get('video')
    reply_to_id = request.POST.get('reply_to')

    if not message_text and not image_file and not video_file:
        return JsonResponse({'success': False, 'error': 'Nothing to send'})

    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat room not found'})

    # Get the reply_to message if provided
    reply_to_message = None
    if reply_to_id:
        try:
            reply_to_message = Message.objects.get(id=reply_to_id, room=room)
        except Message.DoesNotExist:
            pass  # Ignore invalid reply_to_id

    Message.objects.create(
        sender=user,
        room=room,
        content=message_text,
        image=image_file if image_file else None,
        video=video_file if video_file else None,
        reply_to=reply_to_message
    )

    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id, sender=request.user)
        message.delete()
        return JsonResponse({'success': True})
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found or not yours'})

@login_required
def chat_modal_content(request, room_id=None): # Added room_id parameter
    rooms = ChatRoom.objects.filter(participants=request.user).prefetch_related('participants', 'messages')

    # If a chat is opened, remember it in the session
    if room_id:
        request.session['last_chat_room_id'] = room_id

    # If no room_id, try to restore last opened chat from session
    target_room_id = room_id
    if not target_room_id:
        target_room_id = request.GET.get('room_id')
        if not target_room_id:
            last_chat_room_id = request.session.get('last_chat_room_id')
            if last_chat_room_id:
                try:
                    last_room = ChatRoom.objects.get(id=last_chat_room_id, participants=request.user)
                    target_room_id = last_room.id
                except ChatRoom.DoesNotExist:
                    pass
            if not target_room_id and rooms.exists():
                def last_msg_time(room):
                    last_msg = room.messages.order_by('-timestamp').first()
                    return last_msg.timestamp if last_msg else room.id
                most_recent_room = max(rooms, key=last_msg_time)
                target_room_id = most_recent_room.id

    for room in rooms:
        if not room.is_group:
            other = room.participants.exclude(id=request.user.id).first()
            if other:
                user_obj = CustomUser.objects.get(id=other.id)
                room.other_participant = user_obj
            else:                room.other_participant = None
        room.last_message = room.messages.order_by('-timestamp').first()
        if room.last_message:
            room.last_message.is_blocked = is_user_blocked(request.user, room.last_message.sender)
        room.unread_count = room.messages.exclude(sender__id=request.user.id).filter(read=False).count()

    active_room = None
    chat_messages = []
    chat_partner = None

    if target_room_id:
        try:
            target_room_id = int(target_room_id)
            active_room = get_object_or_404(ChatRoom, id=target_room_id, participants=request.user)
            chat_messages = active_room.messages.select_related('sender').order_by('timestamp')
            
            # Add blocking info to messages
            for message in chat_messages:
                message.is_blocked = is_user_blocked(request.user, message.sender)
            
            active_room.messages.exclude(sender__id=request.user.id).update(read=True)

            if not active_room.is_group:
                other = active_room.participants.exclude(id=request.user.id).first()
                if other:
                    user_obj = CustomUser.objects.get(id=other.id)
                    active_room.other_participant = user_obj
                    chat_partner = active_room.other_participant
                else:
                    active_room.other_participant = None
                    chat_partner = None
        except (ValueError, ChatRoom.DoesNotExist):
            pass

    return render(request, 'chat/chat_modal_content.html', {
        'chat_rooms': rooms,
        'active_room': active_room,
        'chat_messages': chat_messages,
        'user': request.user,
        'chat_partner': chat_partner
    })


@require_POST
@csrf_exempt  # If you use AJAX with CSRF token, you can remove this and use @csrf_protect
def create_group_chat(request):
    """Create a new group chat room with a name and participants."""
    data = json.loads(request.body.decode('utf-8'))
    group_name = data.get('group_name')
    participant_ids = data.get('participants', [])
    User = get_user_model()
    if not group_name or not participant_ids:
        return JsonResponse({'error': 'Missing group name or participants.'}, status=400)
    # Always include the creator
    if str(request.user.id) not in participant_ids:
        participant_ids.append(str(request.user.id))
    participants = User.objects.filter(id__in=participant_ids)
    if participants.count() < 2:
        return JsonResponse({'error': 'A group must have at least 2 participants.'}, status=400)
    room = ChatRoom.objects.create(name=group_name, is_group=True)
    room.participants.set(participants)
    room.save()
    return JsonResponse({'success': True, 'room_id': room.id, 'room_name': room.name})

@login_required
@require_POST
def check_blocked_status(request):
    """Check if a user is blocked"""
    try:
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'})
        
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found.'})
        
        # Use the same blocking logic as in views
        is_blocked = Block.objects.filter(
            models.Q(blocker=request.user, blocked=target_user) | 
            models.Q(blocker=target_user, blocked=request.user)
        ).exists()
        
        return JsonResponse({'success': True, 'is_blocked': is_blocked})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
