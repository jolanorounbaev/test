from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ContentItem, VisitedPlace, Achievement, Quote
from registerandlogin.models import CustomUser
from django.shortcuts import get_object_or_404
# Use our own InterestUpdateForm but import friendsearch wordlist for consistency
from .forms import EditProfileForm, ContentItemForm, VisitedPlaceForm, AchievementForm, QuoteForm, InterestUpdateForm
from django.contrib import messages
from django.http import JsonResponse
from friendsearch.wordlist import WORDLIST # Use friendsearch wordlist for consistency
import json
import os
from django.conf import settings
from django.views.decorators.http import require_POST
# Add imports for chat and friend functionality
from chat.models import ChatRoom
from notifications.models import FriendRequest, get_friends
from registerandlogin.models import Report


@login_required
def profile_view(request, user_id=None):
    if user_id:
        profile_user = get_object_or_404(CustomUser, id=user_id)
        is_own_profile = False
    else:
        profile_user = request.user
        is_own_profile = True

    # ✅ Correct reverse relationships using related_name
    visited_places = profile_user.visited_places.all()
    achievements = profile_user.achievements.all()
    quotes = profile_user.quotes.all()
    
    # Check if users have blocked each other
    is_blocked_by_viewer = False
    is_blocked_by_profile_user = False
    if not is_own_profile:
        from .models import Block
        
        # Check if current user blocked the profile user
        is_blocked_by_viewer = Block.objects.filter(
            blocker=request.user, 
            blocked=profile_user
        ).exists()
          # Check if profile user blocked the current user
        is_blocked_by_profile_user = Block.objects.filter(
            blocker=profile_user, 
            blocked=request.user
        ).exists()
        
        # If the profile user blocked you, show limited profile
        if is_blocked_by_profile_user:
            return render(request, 'userprofile/profile_blocked.html', {
                'profile_user': profile_user,
                'blocked_by_them': True,
            })
    
    # Check friendship status and pending requests
    is_friend = False
    pending_request = False
    if not is_own_profile and not is_blocked_by_viewer:
        # Check if they are already friends
        friends = get_friends(request.user)
        is_friend = profile_user in friends
        
        # Check if there's a pending friend request
        pending_request = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=profile_user,
            accepted=False,
            declined=False
        ).exists()
    
    # Get or create chat room for other user's profile
    chat_room_id = None
    if not is_own_profile and not is_blocked_by_viewer and not is_blocked_by_profile_user:
        chat_room = ChatRoom.objects.filter(
            is_group=False, 
            participants=request.user
        ).filter(participants=profile_user).first()
        
        if not chat_room:
            chat_room = ChatRoom.objects.create(is_group=False)
            chat_room.participants.add(request.user, profile_user)
        
        chat_room_id = chat_room.id

    return render(request, 'userprofile/profile.html', {
        'profile_user': profile_user,  # The user whose profile we're viewing
        'current_user': request.user,  # The logged-in user
        'is_own_profile': is_own_profile,  # Boolean to check if viewing own profile
        'is_friend': is_friend,  # Whether users are already friends
        'pending_request': pending_request,  # Whether there's a pending request
        'is_blocked_by_viewer': is_blocked_by_viewer,  # Whether current user blocked profile user
        'visited_places': visited_places,
        'achievements': achievements,
        'quotes': quotes,
        'chat_room_id': chat_room_id,  # Add chat room ID
    })






@login_required
def edit_profile_view(request):
    user = request.user

    profile_form = EditProfileForm(instance=user)
    content_form = ContentItemForm()
    place_form = VisitedPlaceForm()
    achievement_form = AchievementForm()
    quote_form = QuoteForm()

    if request.method == 'POST':
        if 'save_profile' in request.POST and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            profile_form = EditProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile details updated successfully.")
                return redirect('edit_profile')

        elif 'update-interest' in request.POST:
            # Handle interest updates exactly like friendsearch
            print(f"DEBUG: POST data received: {request.POST}")
            print(f"DEBUG: Keys in POST data: {list(request.POST.keys())}")
            
            update_form = InterestUpdateForm(request.POST)
            print(f"DEBUG: Form created, is_valid: {update_form.is_valid()}")
            if not update_form.is_valid():
                print(f"DEBUG: Form errors: {update_form.errors}")
                print(f"DEBUG: Form non-field errors: {update_form.non_field_errors()}")
            
            if update_form.is_valid():
                print(f"DEBUG: Form is valid, cleaned_data: {update_form.cleaned_data}")
                user.interests = update_form.cleaned_data["interests"]
                user.interest_descriptions = {}  # Clear descriptions as this form doesn't handle them
                user.save(update_fields=['interests', 'interest_descriptions'])
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Interests updated successfully!',
                    'interests': user.interests
                })
            else:
                errors_dict = {k: [str(e) for e in v] for k, v in update_form.errors.items()}
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Please check your interests and try again.', 
                    'errors': errors_dict
                }, status=400)

        elif 'add_content' in request.POST:
            content_form = ContentItemForm(request.POST, request.FILES)
            if content_form.is_valid():
                item = content_form.save(commit=False)
                item.user = user
                item.save()
                messages.success(request, "Content added.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest': # If called by saveAllProfileForms
                    return JsonResponse({'status': 'success', 'message': 'Content added.'})
                return redirect('edit_profile')
            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return JsonResponse({'status': 'error', 'errors': content_form.errors}, status=400)
            
        elif 'add_achievement' in request.POST:
            achievement_form = AchievementForm(request.POST, request.FILES)
            if achievement_form.is_valid():
                achievement = achievement_form.save(commit=False)
                achievement.user = user
                achievement.save()
                messages.success(request, "Achievement added.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Achievement added.'})
                return redirect('edit_profile')
            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return JsonResponse({'status': 'error', 'errors': achievement_form.errors}, status=400)


        elif 'add_place' in request.POST:
            place_form = VisitedPlaceForm(request.POST, request.FILES)
            if place_form.is_valid():
                new_place = place_form.save(commit=False)
                new_place.user = user
                new_place.save()
                messages.success(request, "Place added.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Place added.'})
                return redirect('edit_profile')
            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return JsonResponse({'status': 'error', 'errors': place_form.errors}, status=400)
            
        elif 'add_quote' in request.POST:
            quote_form = QuoteForm(request.POST)
            if quote_form.is_valid():
                quote = quote_form.save(commit=False)
                quote.user = user
                quote.save()
                messages.success(request, "Quote added.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Quote added.'})
                return redirect('edit_profile')
            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return JsonResponse({'status': 'error', 'errors': quote_form.errors}, status=400)


    user_interests_list_json = json.dumps(user.interests if isinstance(user.interests, list) else [])
    user_interest_details_json = json.dumps(user.interest_descriptions if isinstance(user.interest_descriptions, dict) else {}) # Will be empty after new save

    return render(request, 'userprofile/edit_profile.html', {
        'profile_form': profile_form,
        'content_form': content_form,
        'place_form': place_form,
        'achievement_form': achievement_form,
        'quote_form': quote_form,
        'user_achievements': Achievement.objects.filter(user=user),
        'user_quotes': Quote.objects.filter(user=user),
        'user_interests_list_json': user_interests_list_json, 
        'user_interest_details_json': user_interest_details_json,
        'wordlist_json': json.dumps(WORDLIST),
    })







@login_required
def delete_content_item(request, item_id):
    content = get_object_or_404(ContentItem, id=item_id, user=request.user)
    content.delete()
    return redirect('edit_profile')


@login_required
def delete_place(request, place_id):
    place = get_object_or_404(VisitedPlace, id=place_id, user=request.user)
    place.delete()
    messages.success(request, "Place removed.")
    return redirect('edit_profile')

@login_required
def delete_achievement(request, achievement_id):
    achievement = get_object_or_404(Achievement, id=achievement_id, user=request.user)
    achievement.delete()
    messages.success(request, "Achievement removed.")
    return redirect('edit_profile')

@login_required
def delete_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id, user=request.user)
    quote.delete()
    messages.success(request, "Quote removed.")
    return redirect('edit_profile')

# API view for wordlist, now serves WORDLIST from friendsearch
def get_word_list_api(request):
    return JsonResponse(WORDLIST, safe=False)

@login_required
@require_POST
def remove_profile_picture(request):
    user = request.user
    if user.profile_picture:
        user.profile_picture.delete(save=False)  # Delete the file from storage
        user.profile_picture = None
        user.save(update_fields=["profile_picture"])
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "no_picture"}, status=400)

@login_required
@require_POST
def report_user(request):
    try:
        # Debug: Print request data
        print(f"POST data: {request.POST}")
        print(f"User authenticated: {request.user.is_authenticated}")
        
        reported_user_id = request.POST.get('reported_user_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')

        if not reported_user_id or not reason:
            return JsonResponse({'success': False, 'message': f'Missing required fields. reported_user_id: {reported_user_id}, reason: {reason}'})

        try:
            reported_user = get_object_or_404(CustomUser, id=reported_user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'User with ID {reported_user_id} not found.'})
        
        if reported_user == request.user:
            return JsonResponse({'success': False, 'message': "You can't report yourself."})

        # Check if already reported for this reason
        existing_report = Report.objects.filter(
            reporter=request.user,
            reported_user=reported_user,
            reason=reason
        ).exists()

        if existing_report:
            return JsonResponse({'success': False, 'message': 'You have already reported this user for this reason.'})

        # Create the report
        report = Report.objects.create(
            reporter=request.user,
            reported_user=reported_user,
            reason=reason,
            description=description
        )
        
        print(f"Report created successfully: {report}")
        return JsonResponse({'success': True, 'message': 'Report submitted successfully.'})

    except Exception as e:
        print(f"Exception in report_user: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})


@login_required
@require_POST
def block_user(request):
    """Block or unblock a user"""
    try:
        user_id = request.POST.get('user_id')
        action = request.POST.get('action', 'block')  # 'block' or 'unblock'
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'})
        
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found.'})
        
        # Prevent self-blocking
        if target_user == request.user:
            return JsonResponse({'success': False, 'message': 'You cannot block yourself.'})
        
        from .models import Block
        
        if action == 'block':
            # Check if already blocked
            existing_block = Block.objects.filter(
                blocker=request.user, 
                blocked=target_user
            ).first()
            
            if existing_block:
                return JsonResponse({'success': False, 'message': 'User is already blocked.'})
              # Create the block
            block = Block.objects.create(
                blocker=request.user,
                blocked=target_user,
                reason=request.POST.get('reason', '')
            )
            
            # Send real-time update to chat interfaces
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            # Notify both users about the block (for real-time chat updates)
            for user_id in [request.user.id, target_user.id]:
                chat_notify_group = f"chat_notify_{user_id}"
                async_to_sync(channel_layer.group_send)(
                    chat_notify_group,
                    {
                        "type": "chat_notify",
                        "content": {
                            "type": "user_blocked",
                            "blocker_id": request.user.id,
                            "blocked_id": target_user.id,
                            "action": "block"
                        }
                    }
                )
            
            # Remove friend connection if they were friends
            from notifications.models import FriendRequest
            
            # Remove any existing friend requests between them
            FriendRequest.objects.filter(
                from_user=request.user, to_user=target_user
            ).delete()
            FriendRequest.objects.filter(
                from_user=target_user, to_user=request.user
            ).delete()
              # Note: You might also want to remove them from each other's friends list
            # This depends on how your friend system works
            
            return JsonResponse({
                'success': True, 
                'message': f'You have blocked {target_user.full_name or target_user.email}.',
                'action': 'blocked'
            })
        
        elif action == 'unblock':
            # Find and remove the block
            try:
                block = Block.objects.get(
                    blocker=request.user, 
                    blocked=target_user
                )
                block.delete()
                
                # Send real-time update to chat interfaces
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                
                # Notify both users about the unblock (for real-time chat updates)
                for user_id in [request.user.id, target_user.id]:
                    chat_notify_group = f"chat_notify_{user_id}"
                    async_to_sync(channel_layer.group_send)(
                        chat_notify_group,
                        {
                            "type": "chat_notify",
                            "content": {
                                "type": "user_blocked",
                                "blocker_id": request.user.id,
                                "blocked_id": target_user.id,
                                "action": "unblock"
                            }
                        }
                    )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'You have unblocked {target_user.full_name or target_user.email}.',
                    'action': 'unblocked'
                })
            except Block.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User is not blocked.'})
        
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action.'})
            
    except Exception as e:
        print(f"Exception in block_user: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})


@login_required
def blocked_users_list(request):
    """View to show all blocked users"""
    from .models import Block
    
    blocked_users = Block.objects.filter(blocker=request.user).select_related('blocked')
    
    context = {
        'blocked_users': blocked_users,
    }
    
    return render(request, 'userprofile/blocked_users.html', context)
