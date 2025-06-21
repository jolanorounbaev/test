from django.contrib.gis.geos import Point
from django.shortcuts import render, redirect
from registerandlogin.models import CustomUser
from django.contrib.gis.measure import D
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import logging
import json
from .wordlist import WORDLIST, autocomplete_suggestions, enhanced_autocomplete_suggestions  
# Ensure InterestUpdateForm and InterestSearchForm are imported
from .forms import InterestUpdateForm, InterestSearchForm 
import re
from datetime import date
logger = logging.getLogger(__name__)
import copy
from django.db import models
from registerandlogin.choices import EUROPEAN_LANGUAGES as LANGUAGE_CHOICES
from notifications.models import FriendRequest
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from chat.models import ChatRoom

def calculate_match_score(user1, user2):
    score = 0
    total_points = 10  # Total possible points

    # Interests matching (up to 6 points - 2 points per common interest)
    user1_interests = set([i.lower() for i in user1.interests if i])
    user2_interests = set([i.lower() for i in user2.interests if i])
    common_interests = user1_interests.intersection(user2_interests)
    interest_score = min(len(common_interests) * 2, 6)  # Max 6 points for interests
    score += interest_score

    # Language matching (2 points if same language)
    if hasattr(user1, 'main_language') and hasattr(user2, 'main_language'):
        if user1.main_language and user2.main_language and user1.main_language == user2.main_language:
            score += 2

    # Age compatibility (2 points for similar age)
    if user1.get_age() and user2.get_age():
        age_diff = abs(user1.get_age() - user2.get_age())
        if age_diff <= 2:
            score += 2
        elif age_diff <= 5:
            score += 1

    return round((score / total_points) * 100)

def get_language_code_from_label(label):
    if not label:
        return None
    label = label.strip().lower()

    # If it's already a valid language code, return it immediately
    valid_codes = [code for code, _ in LANGUAGE_CHOICES]
    if label in valid_codes:
        return label

    # Otherwise match by full label name
    for code, name in LANGUAGE_CHOICES:
        if name.strip().lower() == label:
            return code
    return None

@login_required
def friend_search_view(request):
    print(f"🔍 [DEBUG] friend_search_view called with method: {request.method}")
    print(f"🔍 [DEBUG] GET params: {dict(request.GET)}")
    print(f"🔍 [DEBUG] POST params: {dict(request.POST)}")
    
    user = request.user
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    results = None

    # --- Initial data for forms ---
    user_actual_interests = getattr(user, 'interests', []) or []
    update_form_initial = {
        'interest_1': user_actual_interests[0] if len(user_actual_interests) > 0 else '',
        'interest_2': user_actual_interests[1] if len(user_actual_interests) > 1 else '',
        'interest_3': user_actual_interests[2] if len(user_actual_interests) > 2 else '',
    }

    # Preferred search interests (for "Set Search Preferences" modal's interest fields)
    # and for pre-filling the main search form's interest fields.
    preferred_interests_list = getattr(user, 'preferred_search_interests', []) or []
    pref_update_form_initial = { # For the modal's interest section
        'interest_1': preferred_interests_list[0] if len(preferred_interests_list) > 0 else '',
        'interest_2': preferred_interests_list[1] if len(preferred_interests_list) > 1 else '',
        'interest_3': preferred_interests_list[2] if len(preferred_interests_list) > 2 else '',
    }

    # Initial data for the main search form (pre-filled from preferences)
    # and for the non-interest fields in "Set Search Preferences" modal
    search_form_initial = {
        'interest_1': preferred_interests_list[0] if len(preferred_interests_list) > 0 else '',
        'interest_2': preferred_interests_list[1] if len(preferred_interests_list) > 1 else '',
        'interest_3': preferred_interests_list[2] if len(preferred_interests_list) > 2 else '',
        'main_language': getattr(user, 'preferred_search_language', None),
        'radius_km': getattr(user, 'preferred_search_radius_km', 10), # Default to 10km
        'age_filtering_mode': getattr(user, 'preferred_search_age_mode', None),
    }

    # --- Instantiate forms with initial data ---
    # These may be overridden by POST/GET specific logic below
    update_form = InterestUpdateForm(prefix="update", initial=update_form_initial)    # For "Set Search Preferences" modal's interest fields. Uses "pref" prefix.
    pref_update_form = InterestUpdateForm(prefix="pref", initial=pref_update_form_initial)
    # For standalone search and other fields in "Set Search Preferences" modal.
    search_form = InterestSearchForm(prefix="search", initial=search_form_initial)

    if request.method == 'POST':
        print(f"🔍 [DEBUG] POST request detected")
        print(f"🔍 [DEBUG] POST keys: {list(request.POST.keys())}")
        
        # 📍 Update location
        if 'latitude' in request.POST and 'longitude' in request.POST:
            try:
                lat = float(str(request.POST.get('latitude')).replace(",", ".").strip())
                lon = float(str(request.POST.get('longitude')).replace(",", ".").strip())
                user.location = Point(lon, lat)
                user.save()
                messages.success(request, "📍 Location successfully saved!")
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Location successfully saved'})
                return redirect('friend_search')
            except (ValueError, TypeError):
                messages.error(request, "⚠️ Couldn't fetch location.")
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Couldn't fetch location"})
                return redirect('friend_search')
        
        # 📝 Update user's own interests (from "Edit My Details" modal)
        elif 'update-interest' in request.POST:
            print(f"🔍 [DEBUG] Processing 'update-interest' POST request")
            update_form = InterestUpdateForm(request.POST, prefix="update") # Re-bind with POST
            print(f"🔍 [DEBUG] Update form valid: {update_form.is_valid()}")
            if not update_form.is_valid():
                print(f"🔍 [DEBUG] Update form errors: {update_form.errors}")
            if update_form.is_valid():
                user.interests = update_form.cleaned_data["interests"]
                user.interest_descriptions = {}  # Clear descriptions as this form doesn't handle them
                user.save(update_fields=['interests', 'interest_descriptions'])
                messages.success(request, "✅ Interests updated successfully!")
                
                # Return JSON response for AJAX requests
                if is_ajax:
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Interests updated successfully!',
                        'interests': user.interests
                    })
            else:
                # Return JSON error response for AJAX requests
                if is_ajax:
                    errors_dict = {k: [str(e) for e in v] for k, v in update_form.errors.items()}
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Please check your interests and try again.', 
                        'errors': errors_dict
                    }, status=400)
                # else: errors will be in update_form for rendering

        # ✏️ Update description (from "Edit My Details" modal)
        elif 'description' in request.POST:
            new_description = request.POST.get('description', '').strip()
            if new_description != user.description:
                user.description = new_description
                user.save()
                messages.success(request, "📝 Description updated!")
            else:
                messages.info(request, "No changes made to description.")
            # Forms for response context remain based on initial data unless rebound

        # ⚙️ Save Search Preferences (from "Set Search Preferences" modal)
        elif request.POST.get('save_search_preferences') == '1':
            # Interests for preferences come from fields prefixed "pref-"
            posted_pref_interest_form = InterestUpdateForm(request.POST, prefix="pref")
            # Other preferences come from fields prefixed "search-"
            posted_pref_other_form = InterestSearchForm(request.POST, prefix="search")

            pref_update_form = posted_pref_interest_form # Use posted form for error display
            search_form = posted_pref_other_form      # Use posted form for error display

            if posted_pref_interest_form.is_valid() and posted_pref_other_form.is_valid():
                user.preferred_search_interests = posted_pref_interest_form.cleaned_data.get("interests", [])
                user.preferred_search_language = posted_pref_other_form.cleaned_data.get("main_language")
                user.preferred_search_radius_km = posted_pref_other_form.cleaned_data.get("radius_km")
                user.preferred_search_age_mode = posted_pref_other_form.cleaned_data.get("age_filtering_mode")
                user.save(update_fields=['preferred_search_interests', 'preferred_search_language', 'preferred_search_radius_km', 'preferred_search_age_mode'])
                messages.success(request, "✅ Your search preferences have been saved!")

                # Update initial data dicts to reflect saved changes
                preferred_interests_list = getattr(user, 'preferred_search_interests', []) or []
                pref_update_form_initial = {
                    'interest_1': preferred_interests_list[0] if len(preferred_interests_list) > 0 else '',
                    'interest_2': preferred_interests_list[1] if len(preferred_interests_list) > 1 else '',
                    'interest_3': preferred_interests_list[2] if len(preferred_interests_list) > 2 else '',
                }
                search_form_initial = {
                    'interest_1': preferred_interests_list[0] if len(preferred_interests_list) > 0 else '',
                    'interest_2': preferred_interests_list[1] if len(preferred_interests_list) > 1 else '',
                    'interest_3': preferred_interests_list[2] if len(preferred_interests_list) > 2 else '',
                    'main_language': getattr(user, 'preferred_search_language', None),
                    'radius_km': getattr(user, 'preferred_search_radius_km', 10),
                    'age_filtering_mode': getattr(user, 'preferred_search_age_mode', None),
                }
                # Re-initialize forms with this new initial data for the response context
                pref_update_form = InterestUpdateForm(prefix="pref", initial=pref_update_form_initial)
                search_form = InterestSearchForm(prefix="search", initial=search_form_initial)
                # update_form (for user's own interests) remains based on user.interests
                user_actual_interests = getattr(user, 'interests', []) or []
                update_form_initial_recheck = { # Recheck initial for user's own interests
                    'interest_1': user_actual_interests[0] if len(user_actual_interests) > 0 else '',
                    'interest_2': user_actual_interests[1] if len(user_actual_interests) > 1 else '',
                    'interest_3': user_actual_interests[2] if len(user_actual_interests) > 2 else '',
                }
                update_form = InterestUpdateForm(prefix="update", initial=update_form_initial_recheck)

            else: # Invalid preference forms
                if posted_pref_interest_form.errors:
                    for field, errors_list in posted_pref_interest_form.errors.items():
                        for error in errors_list: messages.error(request, f"Preferred Interests Error ({field}): {error}")
                if posted_pref_other_form.errors:
                    for field, errors_list in posted_pref_other_form.errors.items():
                        for error in errors_list: messages.error(request, f"Other Preferences Error ({field}): {error}")
          # Common AJAX response for POSTs that modify data and re-render page portions
        if is_ajax and not (request.POST.get('latitude') and request.POST.get('longitude')): # Exclude location as it has its own JSON response
            # Return JSON response for AJAX requests
            return JsonResponse({
                'success': True,
                'message': 'Data saved successfully',
                'saved_search_preferences': {
                    'interests': getattr(user, 'preferred_search_interests', []),
                    'language': getattr(user, 'preferred_search_language', ''),
                    'age_mode': getattr(user, 'preferred_search_age_mode', ''),
                    'radius': getattr(user, 'preferred_search_radius_km', None),
                }
            })
        # For non-AJAX POSTs that don't redirect (e.g., form validation errors), they fall through to the final render.
        # If a non-AJAX POST was successful and should show updated page, it should redirect.
        # Example: successful description update, interest update, or preference save could redirect if not AJAX.
        # For now, matching existing pattern: successful POSTs that are not location update and are not AJAX will fall through.
        # Consider adding redirects for non-AJAX success for these too for PRG pattern.
        # e.g. after successful 'update-interest' or 'description' or 'save_search_preferences' if not is_ajax: return redirect('friend_search')
        
    # --- GET Request Handling (Actual Search or Page Load) ---    elif request.method == 'GET':
        print(f"🔍 [DEBUG] GET request processing started")
        if request.GET: # If there are GET parameters, it's an attempt to search
            print(f"🔍 [DEBUG] GET request with parameters: {dict(request.GET)}")
            
            # Create a modified request.GET that uses the form field names without prefixes
            # This is to handle the search form that uses prefixed field names
            modified_get = request.GET.copy()
            
            # Map prefixed search form field names to expected form field names
            for i in range(1, 4):
                search_key = f'search-interest_{i}'
                if search_key in modified_get:
                    modified_get[f'interest_{i}'] = modified_get[search_key]
                    
            for field in ['main_language', 'radius_km', 'age_filtering_mode']:
                search_key = f'search-{field}'
                if search_key in modified_get:
                    modified_get[field] = modified_get[search_key]
            
            search_form = InterestSearchForm(modified_get, prefix="search") # Bind to modified GET data
            print(f"🔍 [DEBUG] Search form created, about to validate...")
            print(f"🔍 [DEBUG] Search form valid: {search_form.is_valid()}")
            if not search_form.is_valid():
                print(f"🔍 [DEBUG] Form errors: {search_form.errors}")
                print(f"🔍 [DEBUG] Form non-field errors: {search_form.non_field_errors()}")
            if not user.location:
                if not any(str(m) == "You have no location set!" and m.level_tag == 'warning' for m in messages.get_messages(request)):
                    messages.warning(request, "You have no location set!")
                results = []
            elif search_form.is_valid():
                typed_interests = search_form.cleaned_data.get("interests", [])
                print(f"🔍 [DEBUG] Cleaned interests from form: {typed_interests}")
                print(f"🔍 [DEBUG] Individual fields: 1='{search_form.cleaned_data.get('interest_1')}', 2='{search_form.cleaned_data.get('interest_2')}', 3='{search_form.cleaned_data.get('interest_3')}'")
                if not any(typed_interests): # Check if typed_interests itself is empty or contains only empty strings
                    # Check if any of the individual interest fields were actually filled
                    if not (search_form.cleaned_data.get("interest_1") or \
                            search_form.cleaned_data.get("interest_2") or \
                            search_form.cleaned_data.get("interest_3")):
                        messages.warning(request, "Please enter at least one interest to search.")
                    results = [] # No results if no interests are provided
                else:
                    # Ensure typed_interests only contains actual values
                    typed_interests = [i for i in typed_interests if i and i.strip()]
                    if not typed_interests: # If after stripping, it's empty
                        messages.warning(request, "Please enter at least one valid interest to search.")
                        results = []
                    else:
                        language_label = search_form.cleaned_data.get("main_language")
                        language_code = get_language_code_from_label(language_label)
                        radius = search_form.cleaned_data.get("radius_km")
                        if radius: radius = int(radius)
                        age_mode = search_form.cleaned_data.get("age_filtering_mode")

                        user_for_scoring = copy.copy(user) # Create a temporary user object for scoring
                        user_for_scoring.interests = typed_interests
                        user_for_scoring.main_language = language_code or language_label # Use code if available
                        
                        filters = Q()
                        if language_code: 
                            filters &= Q(main_language=language_code)
                        if age_mode and user.get_age():
                            user_age = user.get_age()
                            today = date.today()
                            if age_mode == "strict":
                                dob_min = date(today.year - (user_age + 2), today.month, today.day)
                                dob_max = date(today.year - (user_age - 2), today.month, today.day)
                                filters &= Q(date_of_birth__range=(dob_min, dob_max))
                            elif age_mode == "relaxed":
                                dob_min = date(today.year - (user_age + 5), today.month, today.day)
                                dob_max = date(today.year - (user_age - 5), today.month, today.day)
                                filters &= Q(date_of_birth__range=(dob_min, dob_max))
                        
                        if radius and user.location:
                            filters &= Q(location__distance_lte=(user.location, D(km=radius)))
                        
                        # Exclude self, apply filters
                        raw_users = CustomUser.objects.exclude(id=user.id).filter(filters).distinct()
                        
                        # Exclude blocked users
                        from userprofile.models import Block
                        # Exclude users the current user has blocked
                        blocked_by_user = Block.objects.filter(blocker=user).values_list('blocked_id', flat=True)
                        # Exclude users who have blocked the current user
                        blocked_current_user = Block.objects.filter(blocked=user).values_list('blocker_id', flat=True)
                        # Combine both exclusions
                        all_blocked_ids = list(blocked_by_user) + list(blocked_current_user)
                        if all_blocked_ids:
                            raw_users = raw_users.exclude(id__in=all_blocked_ids)
                        
                        # DEBUG: Log search criteria and initial results
                        print(f"🔍 [DEBUG] Search criteria:")
                        print(f"  - Typed interests: {typed_interests}")
                        print(f"  - Language filter: {language_code}")
                        print(f"  - Age mode: {age_mode}")
                        print(f"  - Radius: {radius}")
                        print(f"  - User location: {user.location}")
                          # DEBUG: First, let's see how many users exist total
                        all_users = CustomUser.objects.exclude(id=user.id)
                        print(f"  - Total users in DB (excluding self): {all_users.count()}")
                        print(f"  - Current user ID: {user.id}, name: {user.first_name}")
                        
                        # Exclude self, apply filters
                        raw_users = CustomUser.objects.exclude(id=user.id).filter(filters).distinct()
                        print(f"  - Raw users count (before interest filtering): {raw_users.count()}")
                          # DEBUG: Let's see what interests the first few users have
                        for i, raw_user in enumerate(raw_users[:3]):
                            user_interests = getattr(raw_user, 'interests', []) or []
                            print(f"  - User {i+1} (ID: {raw_user.id}, {raw_user.first_name}): interests = {user_interests}")
                        
                        processed_results = []
                        seen_pairs = set()
                        interest_match_count = 0
                        score_filter_count = 0
                        
                        for other_user in raw_users:
                            # Interest matching: check if 'other_user' has AT LEAST ONE of the 'typed_interests'
                            other_user_interests_set = set(i.lower() for i in (getattr(other_user, 'interests', []) or []))
                            typed_interests_set = set(i.lower() for i in typed_interests if i) # Ensure typed_interests are lowercased for comparison
                              # DEBUG: Log interest matching for first few users
                            if len(processed_results) < 3:
                                print(f"  - User {other_user.first_name} (ID: {other_user.id}) interests: {other_user_interests_set}")
                                print(f"  - Search interests: {typed_interests_set}")
                                print(f"  - Intersection: {typed_interests_set.intersection(other_user_interests_set)}")
                                print(f"  - Is this the same user as searcher? {other_user.id == user.id}")
                            
                            if not typed_interests_set.intersection(other_user_interests_set):
                                continue # Skip if no common interests based on search criteria
                            
                            interest_match_count += 1
                            score = calculate_match_score(user_for_scoring, other_user)
                            print(f"  - User {other_user.first_name} (ID: {other_user.id}) scored: {score}")
                            if score > 0: # Or some threshold
                                score_filter_count += 1
                                pair_key = tuple(sorted([user.id, other_user.id]))
                                if pair_key in seen_pairs: continue
                                seen_pairs.add(pair_key)
                                
                                chat_room = ChatRoom.objects.filter(is_group=False, participants=user).filter(participants=other_user).first()
                                if not chat_room:
                                    chat_room = ChatRoom.objects.create(is_group=False)
                                    chat_room.participants.add(user, other_user)
                                processed_results.append({
                                    'user': other_user, 
                                    'score': score, 
                                    'chat_room_id': chat_room.id
                                })
                        
                        print(f"  - Users with matching interests: {interest_match_count}")
                        print(f"  - Users with score > 0: {score_filter_count}")
                        print(f"  - Final results count: {len(processed_results)}")
                        
                        results = sorted(processed_results, key=lambda x: x['score'], reverse=True)
            else: # Invalid search form on GET
                results = [] # Errors will be in search_form
        # else: No GET parameters, it's a fresh page load.
        # search_form is already initialized with preferences.
        # update_form and pref_update_form are also initialized.
        
    # --- Final Context and Render ---
    context = {
        'update_form': update_form, # For "Edit My Details" (user's own interests)
        'pref_update_form': pref_update_form, # For "Set Search Preferences" (preferred interests section)
        'search_form': search_form, # For standalone search and other fields in "Set Search Preferences"
        'results': results,
        'wordlist_json': json.dumps(WORDLIST),
        'saved_search_preferences': { # Explicitly pass for template if needed beyond forms
            'interests': getattr(user, 'preferred_search_interests', []),
            'language': getattr(user, 'preferred_search_language', ''),
            'age_mode': getattr(user, 'preferred_search_age_mode', ''),
            'radius': getattr(user, 'preferred_search_radius_km', None),
        }
    }
    return render(request, "friendsearch/friend_search.html", context)

@login_required
def edit_interests_inline(request):
    if request.method == "POST":
        form = InterestUpdateForm(request.POST)
        valid_words = [word.lower() for word in WORDLIST]

        if form.is_valid():
            cleaned = form.cleaned_data["interests"]
            # Remove duplicates by converting to a set and back to a list
            cleaned = list(set(cleaned))

            invalids = [i for i in cleaned if i.lower() not in valid_words]

            if invalids:
                form.add_error(None, f"❌ Invalid interest(s): {', '.join(invalids)}")
                return render(request, "friendsearch/friend_search.html", {
                    "form": form,
                    "wordlist_json": json.dumps(WORDLIST),
                    "results": None
                })
            else:
                request.user.interests = cleaned
                request.user.save()
                messages.success(request, "✅ Interests updated successfully!")
                return redirect("friend_search")

    return redirect("friend_search")

@login_required
@login_required
def your_friends(request):
    from notifications.models import get_friends, FriendRequest
    
    # Get user's friends
    friends = get_friends(request.user)
    
    # Get pending friend requests
    friend_requests = FriendRequest.objects.filter(
        to_user=request.user, 
        accepted=False, 
        declined=False
    ).select_related('from_user').order_by('-timestamp')
    
    context = {
        'friends': friends,
        'friend_requests': friend_requests,
        'friend_requests_count': friend_requests.count(),
    }
    
    return render(request, 'friendsearch/your_friends.html', context)

def autocomplete_view(request):
    query = request.GET.get('q', '').strip().lower()
    if not query or len(query) > 50:
        return JsonResponse([], safe=False)

    try:
        # 1. Primary source: Wordlist (highest priority)
        wordlist_suggestions = enhanced_autocomplete_suggestions(query, max_results=15)
        
        # For debugging - let's add some logging
        print(f"🔍 [AUTOCOMPLETE] Query: '{query}', Found {len(wordlist_suggestions)} suggestions")
        print(f"🔍 [AUTOCOMPLETE] First 5 suggestions: {wordlist_suggestions[:5]}")
        
        # Return the suggestions directly (Typeahead expects a simple array)
        return JsonResponse(wordlist_suggestions, safe=False)
        
    except Exception as e:
        print(f"🔍 [AUTOCOMPLETE ERROR] {e}")
        # Fallback to basic wordlist search
        basic_suggestions = autocomplete_suggestions(query, max_results=15)
        return JsonResponse(basic_suggestions, safe=False)

@login_required
@require_POST
def send_friend_request(request):
    try:
        user_id_raw = request.POST.get('user_id')
        if user_id_raw is None:
            raise ValueError("Missing user_id")

        target_user_id = int(user_id_raw)

        if target_user_id == request.user.id:
            return JsonResponse({'success': False, 'message': "You can't add yourself."})

        User = get_user_model()
        to_user = User.objects.get(id=target_user_id)

        if FriendRequest.objects.filter(
            from_user=request.user.id,
            to_user=to_user.id,
            accepted=False,
            declined=False
        ).exists():
            return JsonResponse({'success': False, 'message': 'Request already sent.'})

        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return JsonResponse({'success': True, 'message': 'Friend request sent!'})

    except ValueError as e:
        return JsonResponse({'success': False, 'message': f'Invalid input: {str(e)}'})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})

@login_required
def search_people(request):
    """Search for people in the database"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Search users by name or email (excluding current user)
    users = CustomUser.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) | 
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:20]  # Limit to 20 results
    
    # Convert to JSON-serializable format
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email,
            'bio': user.bio,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        })
    
    return JsonResponse({'users': users_data})

@login_required
@require_POST
def remove_friend(request, friend_id):
    """Remove a friend from user's friend list"""
    from notifications.models import Friendship
    
    try:
        friend = CustomUser.objects.get(id=friend_id)
        
        # Remove friendship in both directions
        Friendship.objects.filter(
            Q(user1=request.user, user2=friend) | 
            Q(user1=friend, user2=request.user)
        ).delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'{friend.full_name} has been removed from your friends.'
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@login_required
def friend_requests_json(request):
    """Get friend requests as JSON for AJAX calls"""
    requests = FriendRequest.objects.filter(
        to_user=request.user, 
        accepted=False, 
        declined=False
    ).select_related('from_user').order_by('-timestamp')
    
    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'from_user': {
                'id': req.from_user.id,
                'first_name': req.from_user.first_name,
                'last_name': req.from_user.last_name,
                'full_name': req.from_user.full_name,
                'profile_picture': req.from_user.profile_picture.url if req.from_user.profile_picture else None,
            },
            'timestamp': req.timestamp.isoformat(),
        })
    
    return JsonResponse({'requests': requests_data})
