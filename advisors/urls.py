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
    path("api/v1/auth/signup/", SignupView.as_view(), name="signup"),
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("api/v1/auth/reset-password/<str:uid>/<str:token>/", ResetPasswordView.as_view(), name="reset-password"),
    
    path("api/v1/customers/create/", create_customer, name="create_customer"),  # NEW
    path("api/v1/customers/<int:customer_id>/", customer_detail, name="customer-detail"),
    
    path("api/v1/ai/context/<int:customer_id>/", CustomerContextView.as_view(), name="customer-context"),
    path("api/v1/ai/question-suggestions/", QuestionSuggestionsView.as_view(), name="question-suggestions"),
    path("api/v1/ai/missing-information/<int:customer_id>/", MissingInformationView.as_view(), name="missing-information"),
    path("api/v1/ai/qualification-insights/", generate_qualification_insights, name="generate_qualification_insights"),
    path("api/v1/ai/qualification-insights/<int:customer_id>/", get_qualification_insights, name="get_qualification_insights"),
    path("api/v1/ai/qualification-insights-history/<int:customer_id>/", get_qualification_insights_history, name="get_qualification_insights_history"),
    path("api/v1/ai/chat/", ai_chat, name="ai_chat"),
    
    path("api/v1/customers/<int:customer_id>/ai-logs/", get_ai_logs, name="get_ai_logs"),  # NEW - Module 7
    
    path("api/v1/token/", obtain_auth_token, name="api_token_auth"),
    path("api/v1/ai/output-versions/save/", save_ai_output_version, name="save_ai_output_version"),  # NEW - Module 8
    path("api/v1/customers/<int:customer_id>/ai-output-versions/", get_ai_output_versions, name="get_ai_output_versions"),  # NEW - Module 8
    
    path("api/v1/token/", obtain_auth_token, name="api_token_auth"),
]
