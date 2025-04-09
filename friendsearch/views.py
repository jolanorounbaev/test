from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import render, redirect
from registerandlogin.models import CustomUser
from django.contrib.gis.measure import D
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from notifications.models import FriendRequest, Friendship, Notification
from django.db.models import Q
import logging
logger = logging.getLogger(__name__)

@login_required
def friend_search_view(request):
    user = request.user
    results = None

    # 📍 Update location if "Use My Location" clicked
    if request.method == 'POST' and 'latitude' in request.POST and 'longitude' in request.POST:
        try:
            lat = float(str(request.POST.get('latitude')).replace(",", ".").strip())
            lon = float(str(request.POST.get('longitude')).replace(",", ".").strip())
            user.location = Point(lon, lat)
            user.save()
            messages.success(request, "📍 Location updated successfully!")
            return redirect('friend_search')
        except (ValueError, TypeError):
            messages.error(request, "⚠️ Failed to update location.")

    elif request.method == 'GET':
        # Debugging: log incoming search values
        interest_1 = request.GET.get("interest_1", "").lower()
        interest_2 = request.GET.get("interest_2", "").lower()
        interest_3 = request.GET.get("interest_3", "").lower()

        print("Interest 1:", interest_1)  # Debugging: print interest_1 value
        print("Interest 2:", interest_2)  # Debugging: print interest_2 value
        print("Interest 3:", interest_3)  # Debugging: print interest_3 value

        selected_language = request.GET.get("main_language")
        min_age = int(request.GET.get("age_min", 18))
        max_age = int(request.GET.get("age_max", 99))
        radius_km = int(request.GET.get("radius", 20))

        # Debugging: log the user-selected values for language and age range
        print("Selected Language:", selected_language)
        print("Age Range:", min_age, "to", max_age)
        print("Search Radius (km):", radius_km)

        lat = request.GET.get("latitude", "").replace(",", ".").strip()
        lon = request.GET.get("longitude", "").replace(",", ".").strip()

        # 🌍 Try to use coordinates from GET
        user_location = None
        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                user.location = user_location  # Optional: update saved location
                user.save()
            except (ValueError, TypeError):
                print("⚠️ Location parsing failed from GET")

        # 📍 Fallback: use user's saved location
        if not user_location and user.location:
            user_location = user.location

        # Only start searching if interests or language are selected
        if interest_1 or interest_2 or interest_3 or selected_language:
            qs = CustomUser.objects.exclude(id=user.id).filter(is_active=True)

            # Filter by location if available
            if user_location:
                qs = qs.filter(location__distance_lte=(user_location, D(km=radius_km)))
                qs = qs.annotate(distance=Distance("location", user_location)).order_by("distance")

            # Filter by age
            qs = [u for u in qs if u.get_age() and min_age <= u.get_age() <= max_age]

            search_interests = [i for i in [interest_1, interest_2, interest_3] if i]
            scored_users = []

            for u in qs:
                score = 0
                interest_match_count = 0
                language_match = False

                if isinstance(u.interests, list):
                    user_interests = [x.lower() for x in u.interests if isinstance(x, str)]
                    interest_match_count = sum(
                        1 for i in search_interests if i in user_interests
                    )
                    score += interest_match_count

                if selected_language and u.main_language == selected_language:
                    language_match = True
                    score += 1.5

                if interest_match_count > 0 or language_match:
                    scored_users.append((u, score))

            results = sorted(scored_users, key=lambda x: x[1], reverse=True)

    return render(request, "friendsearch/friend_search.html", {
        "results": results
    })







from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def edit_interests_inline(request):
    if request.method == "POST":
        interests = [
            request.POST.get("interest_1", "").strip(),
            request.POST.get("interest_2", "").strip(),
            request.POST.get("interest_3", "").strip()
        ]
        interests = [i for i in interests if i]
        request.user.interests = interests
        request.user.save()
    return redirect("friend_search")  # or wherever your friend search view is named


@login_required
def your_friends(request):
 return render(request, 'friendsearch/your_friends.html')



from django.http import JsonResponse
from registerandlogin.models import CustomUser
from .wordlist import WORDLIST as wordlist

def autocomplete_view(request):
    query = request.GET.get('q', '').lower()
    suggestions = []

    # Search in predefined wordlist
    suggestions = [word for word in wordlist if query in word.lower()]
    
    # Search in user interests (if needed)
    user_interests = CustomUser.objects.filter(interests__icontains=query).values_list('interests', flat=True)
    suggestions.extend(user_interests)
    
    # Remove duplicates and sort
    suggestions = sorted(list(set(suggestions)))
    
    return JsonResponse(suggestions, safe=False)
    


User = get_user_model()

@login_required
@require_POST
def send_friend_request(request, user_id):
    try:
        # Ensure the request is AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            raise PermissionDenied("This endpoint only accepts AJAX requests")
            
        # Get recipient user
        try:
            recipient = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # Validate request
        if request.user == recipient:
            return JsonResponse({
                'success': False,
                'message': 'You cannot send a friend request to yourself'
            }, status=400)
        
        # Check existing relationships (through Friendship model)
        if Friendship.objects.filter(
            Q(user1=request.user, user2=recipient) | 
            Q(user1=recipient, user2=request.user)
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'This user is already your friend'
            }, status=400)
            
        # Check for existing requests
        existing_request = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=recipient,
            status='pending'
        ).first()
        
        if existing_request:
            return JsonResponse({
                'success': False,
                'message': 'Friend request already sent'
            }, status=400)
            
        # Check for reciprocal request
        reciprocal_request = FriendRequest.objects.filter(
            from_user=recipient,
            to_user=request.user,
            status='pending'
        ).first()
        
        if reciprocal_request:
            return JsonResponse({
                'success': False,
                'message': 'This user has already sent you a friend request'
            }, status=400)
        
        # Create new request
        FriendRequest.objects.create(
            from_user=request.user,
            to_user=recipient,
            status='pending'
        )
        
        # Create notification
        Notification.create_friend_request_notification(request.user, recipient)
        
        return JsonResponse({
            'success': True,
            'message': 'Friend request sent successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in send_friend_request: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'An unexpected error occurred'
        }, status=500)
