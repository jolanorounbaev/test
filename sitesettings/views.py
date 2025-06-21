from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.views.decorators.csrf import csrf_exempt

@login_required
def site_settings(request):
    user = request.user
    # Handle Show My Location toggle
    if request.method == 'POST' and 'show_location' in request.POST:
        show_location = 'show_location' in request.POST
        user.show_location = show_location
        if not show_location:
            user.location = None  # Remove location if toggle is off
            print(f"[DEBUG] Location for user {user.email} set to None via settings toggle.")
        user.save()
        print(f"[DEBUG] User {user.email} location after save: {user.location}")
        messages.success(request, 'Location visibility updated.')
        return redirect('site_settings')
    
    # Get blocked users count for display
    from userprofile.models import Block
    blocked_users_count = Block.objects.filter(blocker=user).count()
    
    context = {
        'blocked_users_count': blocked_users_count,
    }
    return render(request, 'sitesettings/sitesettings.html', context)

@login_required
@csrf_exempt
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('login')
    return redirect('site_settings')
