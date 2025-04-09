from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EditProfileForm, ContentItemForm
from .models import ContentItem
from registerandlogin.models import CustomUser

@login_required
def profile_view(request, user_id=None):
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
    else:
        user = request.user

    return render(request, 'userprofile/profile.html', {
        'user': user
    })

@login_required
def edit_profile_view(request):
    user = request.user

    # Initialize both forms
    profile_form = EditProfileForm(instance=user)
    content_form = ContentItemForm()

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            profile_form = EditProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('profile')

        elif 'add_content' in request.POST:
            content_form = ContentItemForm(request.POST, request.FILES)
            if content_form.is_valid():
                item = content_form.save(commit=False)
                item.user = user
                item.save()
                return redirect('profile')

    return render(request, 'userprofile/edit_profile.html', {
        'profile_form': profile_form,
        'content_form': content_form
    })


from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def delete_content_item(request, item_id):
    content = get_object_or_404(ContentItem, id=item_id, user=request.user)
    content.delete()
    return redirect('profile')
