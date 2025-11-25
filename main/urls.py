from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views
from .views import LoginView, user_profile_page, queue_page, logout_view, login_page

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.Register.as_view(), name='register_api'),
    path('register-page/', views.register_user, name='register_page'),
    path('profile/', user_profile_page, name='user_profile_page'),
    path('queues/', views.queues, name='queues'),
    path('queue/', queue_page, name='queue_page'),
    path('api/queues/', views.QueueListView.as_view(), name='queue_list_api'),
    path('api/queues/<int:pk>/', views.QueueDetailView.as_view(), name='queue_detail_api'),
    path('api/entries/', views.QueueEntryListView.as_view(), name='queue_entries'),
    path('api/entries/<int:pk>/', views.QueueEntryDetailView.as_view(), name='queue_entry_detail'),
    path('api/notifications/', views.NotificationListView.as_view(), name='notifications_list'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_read'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='verify'),
    path('login/', login_page, name='login_page'),
    path('api/login/', LoginView.as_view(), name='login_api'),
    path('logout/', logout_view, name='logout'),
]
