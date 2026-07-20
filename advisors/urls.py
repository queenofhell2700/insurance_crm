# advisors/urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ai_chat,
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
    get_ai_logs,  # NEW - Module 7
    create_customer,  # NEW - missing endpoint
    save_ai_output_version,  # NEW - Module 8
    get_ai_output_versions,  # NEW - Module 8
)

urlpatterns = [
    path("api/v1/auth/signup/", SignupView.as_view(), name="api_signup"),
    path("api/v1/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/v1/auth/forgot-password/", ForgotPasswordView.as_view(), name="api_forgot_password"),
    path("api/v1/auth/reset-password/<str:uid>/<str:token>/", ResetPasswordView.as_view(), name="api_reset_password"),
    
    path("api/v1/customers/create/", create_customer, name="api_create_customer"),
    path("api/v1/customers/<int:customer_id>/", customer_detail, name="api_customer_detail"),
    
    path("api/v1/ai/context/<int:customer_id>/", CustomerContextView.as_view(), name="api_customer_context"),
    path("api/v1/ai/question-suggestions/", QuestionSuggestionsView.as_view(), name="api_question_suggestions"),
    path("api/v1/ai/missing-information/<int:customer_id>/", MissingInformationView.as_view(), name="api_missing_information"),
    path("api/v1/ai/qualification-insights/", generate_qualification_insights, name="api_generate_qualification_insights"),
    path("api/v1/ai/qualification-insights/<int:customer_id>/", get_qualification_insights, name="api_get_qualification_insights"),
    path("api/v1/ai/qualification-insights-history/<int:customer_id>/", get_qualification_insights_history, name="api_get_qualification_insights_history"),
    path("api/v1/ai/chat/", ai_chat, name="api_ai_chat"),
    
    path("api/v1/customers/<int:customer_id>/ai-logs/", get_ai_logs, name="api_get_ai_logs"),
    
    path("api/v1/token/", obtain_auth_token, name="api_token_auth"),
    path("api/v1/ai/output-versions/save/", save_ai_output_version, name="api_save_ai_output_version"),
    path("api/v1/customers/<int:customer_id>/ai-output-versions/", get_ai_output_versions, name="api_get_ai_output_versions"),
]