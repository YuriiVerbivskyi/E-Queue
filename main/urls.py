from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views
from rest_framework import permissions

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.Register.as_view(), name='register_api'),
    path('register-page/', views.register_user, name='register_page'),
    path('profile/', views.user_profile, name='user_profile'),
    path('queues/', views.QueueListView.as_view(), name='queues'),
    path('queues/<int:pk>/', views.QueueDetailView.as_view(), name='queue_detail'),
    path('entries/', views.QueueEntryListView.as_view(), name='queue_entries'),
    path('entries/<int:pk>/', views.QueueEntryDetailView.as_view(), name='queue_entry_detail'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_read'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='verify'),
]
