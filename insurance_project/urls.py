from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from advisors.views import signup_view, login_view, dashboard

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth routes (custom Django views)
    path("login/", login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Dashboard and signup (session-based auth)
    path("dashboard/", dashboard, name="dashboard"),
    path("signup/", signup_view, name="signup"),

    # API routes
    path("", include("advisors.urls")),
]