from django.urls import path
from .views import (
    SignupView,
    LoginView,
    CustomerContextView,
    QuestionSuggestionsView,   # NEW: added import
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    path("api/auth/signup/", SignupView.as_view(), name="signup"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path(
        "api/auth/forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot-password",
    ),
    path(
        "api/auth/reset-password/<str:uid>/<str:token>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    path(
        "api/ai/context/<int:customer_id>/",
        CustomerContextView.as_view(),
        name="customer-context",
    ),
    # NEW: added this path for Module 3
    path(
        "api/ai/question-suggestions/",
        QuestionSuggestionsView.as_view(),
        name="question-suggestions",
    ),
]