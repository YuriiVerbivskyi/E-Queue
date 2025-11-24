from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views
from rest_framework import permissions



urlpatterns = [
    path('queues/', views.queues, name='queues'),
    path('queues/<int:pk>/', views.QueueDetailView.as_view(), name='queue_detail'),
    path('entries/', views.QueueEntryListView.as_view(), name='queue_entries'),
    path('entries/<int:pk>/', views.QueueEntryDetailView.as_view(), name='queue_entry_detail'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='verify'),
    path('register/', views.Register.as_view(), name='register_api'),
    path('login/', views.LoginView.as_view(), name='login_api'),
    path('profile/', views.user_profile, name='user_profile_api'),
    path('profile/', views.user_profile, name='user_profile'),
    path('monoinfo/<str:data>/', views.MonoData.as_view(), name='mono_data'),
    path('', views.home, name='home'),
]
