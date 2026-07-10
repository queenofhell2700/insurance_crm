from .views import ai_chat
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path
from .views import (
    SignupView,
    LoginView,
    CustomerContextView,
    QuestionSuggestionsView,
    ForgotPasswordView,
    ResetPasswordView,
    MissingInformationView,
    customer_detail,
    generate_qualification_insights,
    get_qualification_insights,
    get_qualification_insights_history,
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
    path(
        "api/ai/question-suggestions/",
        QuestionSuggestionsView.as_view(),
        name="question-suggestions",
    ),
    path(
        "api/ai/missing-information/<int:customer_id>/",
        MissingInformationView.as_view(),
        name="missing-information",
    ),
    path(
        "api/customer/<int:customer_id>/",
        customer_detail,
        name="customer-detail",
    ),
    path(
        "api/ai/qualification-insights/",
        generate_qualification_insights,
        name="generate_qualification_insights",
    ),
    path(
        "api/ai/qualification-insights/<int:customer_id>/",
        get_qualification_insights,
        name="get_qualification_insights",
    ),
    path(
        "api/ai/qualification-insights-history/<int:customer_id>/",
        get_qualification_insights_history,
        name="get_qualification_insights_history",
    ),
    path("api/ai/chat/", ai_chat, name="ai_chat"), #module 6 new url added
    path("api/token/", obtain_auth_token, name="api_token_auth"), #new
]