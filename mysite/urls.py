from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main import views as main_views

urlpatterns = [
    path('', main_views.home, name='home'),
    path('register/', main_views.register_user, name='register_page'),
    path('profile/', main_views.user_profile_page, name='user_profile'),
    path('login/', main_views.login_page, name='login_page'),
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
