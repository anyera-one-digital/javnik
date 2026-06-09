from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import payment_views, views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/credentials/', views.RegisterCredentialsView.as_view(), name='register_credentials'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_code_view, name='resend_verification'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile_view, name='profile'),
    path('subscription/', views.subscription_view, name='subscription'),
    path(
        'payments/subscription/init/',
        payment_views.subscription_payment_init_view,
        name='subscription_payment_init',
    ),
    path(
        'payments/tbank/notification/',
        payment_views.tbank_notification_view,
        name='tbank_notification',
    ),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('avatar/', views.upload_avatar_view, name='upload_avatar'),
    path('address-suggest/', views.address_suggest_view, name='address_suggest'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path(
        'account/deletion-status/',
        views.account_deletion_status_view,
        name='account_deletion_status',
    ),
    path('account/delete/', views.delete_account_view, name='delete_account'),
]
