"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from userprofile.views import profile_view
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registerandlogin.urls')),
    path('', include('userprofile.urls')),
    path('', profile_view, name='home'),
    path('friendsearch/', include('friendsearch.urls')),
    path('posts/', include('posts.urls')),
    path('chat/', include('chat.urls')),
    path('settings/', include('sitesettings.urls')), 
    path('notifications/', include('notifications.urls')),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
