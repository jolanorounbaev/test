from django.shortcuts import render

def about_me(request):
    return render(request, 'legal_pages/about_me.html')

def privacy_policy(request):
    return render(request, 'legal_pages/privacy_policy.html')

def more_info(request):
    return render(request, 'legal_pages/more_info.html')