from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def site_settings(request):
    return render(request, 'sitesettings/sitesettings.html')
