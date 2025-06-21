from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Moment
from .wordlist import WORDLIST
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Moment, MomentPing
from registerandlogin.models import CustomUser
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Moment, MomentComment, MomentReply
from django.http import HttpResponseForbidden
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from .models import Moment, FireReaction, HeartReaction
from datetime import timedelta
from .models import MomentFlag
# from .forms import MomentForm  # Import the form for editing moments
from django.db import transaction, IntegrityError

from .wordlist import WORDLIST  # Make sure this is your validated interest list

@login_required
def create_moment(request):
    wordlist_json = json.dumps(WORDLIST)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        interests_raw = request.POST.getlist('interests')  # <-- Fix: get all selected interests
        youtube_link = request.POST.get('youtube_link', '').strip()

        media_file = request.FILES.get('media_file')
        image = media_file if media_file and 'image' in media_file.content_type else None
        video = media_file if media_file and 'video' in media_file.content_type else None

        # ✅ Debug print
        print("📷 Image:", image)
        print("🎥 Video:", video)
        print("▶️ YouTube:", youtube_link)
        allowed_interests = set(i.lower() for i in WORDLIST)
        interests = [i.strip() for i in interests_raw if i.strip().lower() in allowed_interests][:3]
        if not interests:
            messages.error(request, "Please pick at least one valid interest.")
            return render(request, 'moments/moment_form.html', {'wordlist_json': wordlist_json}) # Pass wordlist_json

        if not content and not image and not video and not youtube_link:
            messages.error(request, "Moment must contain at least text or media.")
            return render(request, 'moments/moment_form.html', {'wordlist_json': wordlist_json}) # Pass wordlist_json

        # Fix: avoid blocking if empty file fields exist
        if image and video and hasattr(video, 'name') and video.name != '':
            messages.error(request, "You can only upload an image OR a video.")
            return render(request, 'moments/moment_form.html', {'wordlist_json': wordlist_json}) # Pass wordlist_json

        moment = Moment.objects.create(
            user=request.user,
            title=request.POST.get("title", "").strip(),
            content=content,
            image=image if image else None,
            video=video if video else None,
            youtube_link=youtube_link or None,
            interests=interests,
            expires_at=timezone.now() + timezone.timedelta(minutes=20),
            last_active=timezone.now(),
            is_active=True,
        ) 


        print("✅ Moment created:", moment.id)
        messages.success(request, "Moment posted!")
        return redirect('moments:moment_feed')
    else: # GET request
        return render(request, 'moments/moment_form.html', {'wordlist_json': wordlist_json})




@login_required
def moment_feed(request):
    user = request.user
    print("Logged-in user:", user.email)

    # Get interest from query param
    interest_query = request.GET.get('interest', '').strip().lower()

    # Get all active, unexpired Moments
    active_moments = Moment.objects.filter(
        is_active=True,
        flag_count__lt=10,
        expires_at__gt=timezone.now()
    )

    if interest_query:
        # Filter moments by interest (case-insensitive)
        active_moments = active_moments.filter(interests__icontains=interest_query)
        print(f"Filtering moments by interest: {interest_query}")

    print("📋 Moments before location filtering:", active_moments.count())

    # Get "On Fire" moments
    on_fire_moments = Moment.objects.filter(
        is_active=True,
        fire_count__gte=25, # Assuming 25 is the threshold for "on fire"
        expires_at__gt=timezone.now(),
        flag_count__lt=10
    ).order_by('-fire_count', '-created_at')[:5] # Get top 5, for example

    moments_to_display = active_moments.order_by('-created_at') # Keep your existing logic for main feed
    print("Showing all Moments without distance filter")

    # --- Add cooldown info for each moment ---
    fire_cooldowns = {}
    from .models import FireReaction
    from datetime import timedelta
    now = timezone.now()
    for moment in moments_to_display:
        recent_fire = FireReaction.objects.filter(
            user=user,
            moment=moment,
            timestamp__gte=now - timedelta(minutes=30)
        ).order_by('-timestamp').first()
        if recent_fire:
            cooldown_end = recent_fire.timestamp + timedelta(minutes=30)
            seconds_left = int((cooldown_end - now).total_seconds())
            if seconds_left < 0:
                seconds_left = 0
            moment.fire_cooldown_seconds = seconds_left
        else:
            moment.fire_cooldown_seconds = 0

    return render(request, 'moments/feed.html', {
        'moments': moments_to_display,
        'on_fire_moments': on_fire_moments,  # Add this to the context
        'interest_query': interest_query,
        'fire_cooldowns': fire_cooldowns,
    })




@login_required
def ping_user_into_moment(request, moment_id):
    to_user_id = request.POST.get("user_id")
    moment = get_object_or_404(Moment, id=moment_id)
    to_user = get_object_or_404(CustomUser, id=to_user_id)

    if to_user == request.user:
        return JsonResponse({'error': 'You cannot ping yourself'}, status=400)

    ping, created = MomentPing.objects.get_or_create(
        moment=moment,
        from_user=request.user,
        to_user=to_user
    )




@login_required
def interest_wordlist(request):
    return JsonResponse(WORDLIST, safe=False)


@login_required
def join_moment(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id)

    if request.user in moment.participants.all():
        messages.info(request, "You're already in this Moment.")
    elif moment.participants.count() >= moment.max_participants:
        messages.error(request, "This Moment is full.")
    else:
        moment.participants.add(request.user)
        messages.success(request, "✅ You joined the Moment!")

    return redirect('moments:moment_feed')



@login_required
def add_comment(request, moment_id):
    if request.method == "POST":
        moment = get_object_or_404(Moment, id=moment_id)
        content = request.POST.get("content")
        if content:
            MomentComment.objects.create(moment=moment, user=request.user, content=content)
    return redirect('moments:moment_feed')



@login_required
def add_reply(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(MomentComment, id=comment_id)
        content = request.POST.get("content")
        if content:
            MomentReply.objects.create(comment=comment, user=request.user, content=content)
    return redirect('moments:moment_feed')



@login_required
def leave_moment(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id)
    moment.participants.remove(request.user)
    return redirect('moments:moment_feed')



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(MomentComment, id=comment_id)
    if comment.user != request.user and comment.moment.user != request.user:
        return HttpResponseForbidden()
    moment_id = comment.moment.id
    comment.delete()
    return redirect('moments:moment_feed')



@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(MomentReply, id=reply_id)
    if reply.user != request.user and reply.comment.moment.user != request.user:
        return HttpResponseForbidden()
    moment_id = reply.comment.moment.id
    reply.delete()
    return redirect('moments:moment_feed')


@login_required
def delete_moment(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id)

    if moment.user != request.user:
        return HttpResponseForbidden("You're not allowed to delete this moment.")

    moment.delete()
    messages.success(request, "Moment deleted.")
    return redirect('moments:moment_feed')


def load_comments_inline(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id)
    return render(request, "moments/partials/comments_block.html", {
        "moment": moment,
        "readonly": True
    })


@csrf_exempt
def fire_reaction_view(request, moment_id):
    if request.method == 'POST' and request.user.is_authenticated:
        moment = Moment.objects.get(id=moment_id)
        # Only allow one fire per user per moment per 30 minutes
        recent_fire = FireReaction.objects.filter(
            user=request.user,
            moment=moment,
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).order_by('-timestamp').first()
        if recent_fire:
            # Calculate cooldown seconds left
            cooldown_end = recent_fire.timestamp + timedelta(minutes=30)
            seconds_left = int((cooldown_end - timezone.now()).total_seconds())
            if seconds_left < 0:
                seconds_left = 0
            return JsonResponse({
                'status': 'error',
                'message': 'You can only fire once every 30 minutes for this moment.',
                'cooldown_seconds': seconds_left,
                'fire_count': moment.fire_count
            })

        FireReaction.objects.create(user=request.user, moment=moment)
        moment.fire_count += 1
        moment.save()
        return JsonResponse({'status': 'success', 'fire_count': moment.fire_count, 'cooldown_seconds': 1800})
    return JsonResponse({'status': 'error'})


@csrf_exempt
def heart_reaction_view(request, moment_id):
    if request.method == 'POST' and request.user.is_authenticated:
        moment = Moment.objects.get(id=moment_id)
        try:
            with transaction.atomic():
                existing = HeartReaction.objects.select_for_update().filter(user=request.user, moment=moment)
                if existing.exists():
                    existing.delete()
                    moment.heart_count = max(0, moment.heart_count - 1)
                    moment.save()
                    return JsonResponse({'status': 'unliked', 'heart_count': moment.heart_count})
                else:
                    HeartReaction.objects.create(user=request.user, moment=moment)
                    moment.heart_count += 1
                    moment.save()
                    return JsonResponse({'status': 'liked', 'heart_count': moment.heart_count})
        except IntegrityError:
            # If a race condition occurs, just return the current count
            moment.refresh_from_db()
            return JsonResponse({'status': 'liked', 'heart_count': moment.heart_count})
    return JsonResponse({'status': 'error'})


def check_fire_status(request, moment_id):
    if request.user.is_authenticated:
        recent = FireReaction.objects.filter(
            user=request.user,
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).order_by('-timestamp').first()

        if recent:
            time_left = recent.timestamp + timedelta(minutes=30) - timezone.now()
            total_seconds = int(time_left.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return JsonResponse({
                'can_fire': False,
                'cooldown': f"{minutes}m {seconds}s"
            })
        else:
            return JsonResponse({'can_fire': True})
    return JsonResponse({'error': 'Not authenticated'}, status=401)





@login_required
def flag_moment(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id)
    existing_flag = MomentFlag.objects.filter(user=request.user, moment=moment).first()
    
    if not existing_flag:
        MomentFlag.objects.create(user=request.user, moment=moment)
        moment.flag_count += 1
        if moment.flag_count >= 10:
            moment.is_active = False  # Auto-hide
        moment.save()
        return JsonResponse({'status': 'flagged', 'flag_count': moment.flag_count})
    return JsonResponse({'status': 'already_flagged', 'flag_count': moment.flag_count})


@login_required
def edit_moment(request, moment_id):
    moment = get_object_or_404(Moment, id=moment_id, user=request.user)
    if request.method == 'POST':
        # form = MomentForm(request.POST, request.FILES, instance=moment)
        # if form.is_valid():
        #     form.save()
        messages.success(request, 'Moment updated!')
        return redirect('moments:moment_feed')
    else:
        # form = MomentForm(instance=moment)
        pass
    return render(request, 'moments/moment_edit_page.html', {'moment': moment})
