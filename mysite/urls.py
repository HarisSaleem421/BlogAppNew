"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
# from django.urls import include
from django.urls import path
from blog import views
# from blog.views import LogoutView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,    
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('posts/get/', views.post_list_get),
    path('post/new/', views.new_post),
    path('register/', views.register_user),
    path('login/', views.login_user),
    # path('logout/', views.logout_user),
    # path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('posts/<int:id>/', views.post_get),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('author/posts/<int:author_id>/', views.author_posts),
    path('all_users/', views.all_users),
    path('loggedin_user/', views.loggedin_user),
    path('password_reset/', views.password_reset_request),
    path('password_reset_confirm/', views.password_reset_confirm),
    #stripe urls
    path('register/customer/', views.register_customer),
    path('subscription/create/', views.create_subscription),
    path('create_payment_method/', views.create_payment_method),
    path('subscription/update/', views.update_subscription),
    path('subscription/retrieve/<str:subscription_id>/', views.retrieve_subscription),
    path('list/subscriptions/', views.list_subscriptions),
    path('subscription/cancel/', views.cancel_subscription),
    path('subscription/resume/', views.resume_subscription),
]