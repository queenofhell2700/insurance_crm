# new imports for Gemini integration
import json
import google.generativeai as genai
from django.conf import settings

# ADDED: Logger import
import logging
logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
#from .models import Customer
from .models import Customer, Policy, ExistingInsuranceCover #added
from .serializers import AIOutputVersionSerializer, UserSerializer, LoginSerializer

#MODULE 5 IMPORTS
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import QualificationInsight
from .qualification_engine import QualificationEngine

from .chat_service import get_chat_service #mod 6

from .models import AIRequestLog  # NEW - Module 7
from .serializers import AIRequestLogSerializer  # NEW - Module 7
from .models import AIOutputVersion  # NEW - Module 8
from .serializers import AIOutputVersionSerializer  # NEW - Module 8

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from django.contrib.auth import authenticate, login, logout

# ===== ADDED: Django's Built-in LoginView =====
from django.contrib.auth.views import LoginView


# ===== REPLACED: CustomLoginView (Django's built-in, replaces custom login_view) =====
class CustomLoginView(LoginView):
    """
    Use Django's built-in LoginView for reliability and best practices.
    Replaces the previous custom login_view function that had manual auth handling and debug logging.
    """
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = '/dashboard/'


# ===== SIGNUP VIEW (FOR DJANGO AUTH - NOT REST API) =====
@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Handle user signup with form validation"""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        errors = []

        # Validation
        if not username or not email or not password1 or not password2:
            errors.append("All fields are required.")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        elif User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        elif User.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        elif password1 != password2:
            errors.append("Passwords do not match.")
        elif len(password1) < 8:
            errors.append("Password must be at least 8 characters long.")

        if errors:
            return render(request, 'signup.html', {'errors': errors})

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Authenticate and log in the user
        user = authenticate(request, username=username, password=password1)
        login(request, user)

        # Redirect to dashboard
        return redirect('dashboard')

    return render(request, 'signup.html')


# ===== LOGOUT VIEW (NEW) =====
def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')

# ===== DASHBOARD VIEW (UPDATED) =====
@login_required(login_url='login')
def dashboard(request):
    """Render dashboard for authenticated users with customer selection"""

    # Get all customers for this advisor
    customers = Customer.objects.filter(assigned_to=request.user).order_by('-id')
    customers_count = customers.count()
    logs_count = AIRequestLog.objects.filter(customer__assigned_to=request.user).count()
    insights_count = QualificationInsight.objects.filter(customer__assigned_to=request.user).count()
    output_versions_count = AIOutputVersion.objects.filter(customer__assigned_to=request.user).count()

    # Get selected customer (from query param or first customer)
    selected_customer = None
    family_count = 0
    ped_list = []
    missing_info = []
    qualification_insight = None
    ai_output_versions = []

    customer_id = request.GET.get('customer_id')
    if customer_id:
        try:
            selected_customer = Customer.objects.get(id=customer_id, assigned_to=request.user)

            # Get customer details
            family_count = selected_customer.family_members.count()
            ped_list = [d.disease_name for d in selected_customer.medical_disclosures.all()]

            # Get latest qualification insight
            qualification_insight = selected_customer.qualification_insights.first()

            # Get AI output versions for this customer
            ai_output_versions = AIOutputVersion.objects.filter(customer=selected_customer).order_by('-created_at')[:5]

            # Get missing information
            if selected_customer.premium_budget is None:
                missing_info.append("Premium Budget")

            if not selected_customer.preferred_hospitals:
                missing_info.append("Preferred Hospitals")

            insurance_covers = selected_customer.insurance_covers.all()
            if not insurance_covers.exists():
                missing_info.append("Existing Insurance Cover")
            else:
                for cover in insurance_covers:
                    if not cover.claim_history:
                        missing_info.append("Claim History")
                        break

            for disclosure in selected_customer.medical_disclosures.all():
                if not disclosure.hospitalization_history:
                    missing_info.append("Hospitalization History")
                    break

            if not selected_customer.family_members.exists():
                missing_info.append("Family Information")

        except Customer.DoesNotExist:
            pass

    context = {
        "customers_count": customers_count,
        "logs_count": logs_count,
        "insights_count": insights_count,
        "output_versions_count": output_versions_count,
        "recent_customers": customers[:5],
        "all_customers": customers,  # NEW - For sidebar listing
        "selected_customer": selected_customer,  # NEW
        "family_count": family_count,  # NEW
        "ped_list": ped_list,  # NEW
        "missing_info": missing_info,  # NEW
        "qualification_insight": qualification_insight,  # NEW
        "ai_output_versions": ai_output_versions,  # NEW
    }
    return render(request, "dashboard.html", context)


# ===== REST API VIEWS (KEEP ALL UNCHANGED) =====

class CustomerContextView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id, assigned_to=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Customer not found or access denied", "data": None},
                status=status.HTTP_404_NOT_FOUND,
            )

        cover = customer.insurance_covers.first()

        return Response({
            "status": "success",
            "message": "Customer context retrieved",
            "data": {
                "name": customer.full_name,
                "age": customer.age,
                "city": customer.city,
                "family_members": customer.family_members.count(),
                "ped": [d.disease_name for d in customer.medical_disclosures.all()],
                "existing_cover": float(cover.coverage_amount) if cover else 0,
            }
        })


class QuestionSuggestionsView(APIView):
    def post(self, request):
        customer_id = request.data.get("customer_id")
        try:
            customer = Customer.objects.get(id=customer_id, assigned_to=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Customer not found or access denied", "data": None},
                status=status.HTTP_404_NOT_FOUND,
            )

        diseases = [d.disease_name for d in customer.medical_disclosures.all()]
        cover = customer.insurance_covers.first()
        cover_amount = float(cover.coverage_amount) if cover else 0
        family_count = customer.family_members.count()

        prompt = f"""You are an insurance advisor assistant. Based on this customer profile, suggest 3-5 follow-up questions the advisor should ask, with a reason for each.

    Customer:
    - Age: {customer.age}
    - City: {customer.city}
    - Family members: {family_count}
    - Pre-existing diseases: {diseases if diseases else "None declared"}
    - Existing coverage: ₹{cover_amount}

    Respond ONLY with valid JSON, no markdown, no backticks, no preamble. Format exactly like this:
    {{"questions": [{{"question": "...", "reason": "..."}}]}}"""

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content(prompt)

            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            ai_data = json.loads(raw_text)

            # NEW - Module 7 logging (success)
            AIRequestLog.objects.create(
                customer=customer,
                user=request.user,
                log_type='question_suggestion',
                prompt_text=prompt,
                response_text=raw_text,
                model_name='gemini-flash-latest',
                status='success'
            )

            # NEW - Module 8 versioning
            latest_version = AIOutputVersion.objects.filter(
                customer=customer,
                output_type='question_suggestion'
            ).order_by('-version_number').first()
            next_version = (latest_version.version_number + 1) if latest_version else 1

            AIOutputVersion.objects.create(
                customer=customer,
                output_type='question_suggestion',
                version_number=next_version,
                response_json=ai_data,
                model_used='gemini-flash-latest'
            )

            return Response({
                "status": "success",
                "message": "Questions generated via Gemini",
                "data": {
                    "confidence": 0.85,
                    "questions": ai_data.get("questions", []),
                    "source": "gemini"
                }
            })

        except Exception as e:
            questions = []

            if customer.age > 55:
                questions += [
                    {"question": "Do you have any pre-existing medical conditions?", "reason": "High age increases health risk relevance."},
                    {"question": "Have you been hospitalized in the last 2 years?", "reason": "Recent hospitalization affects risk assessment."},
                ]

            for disease in customer.medical_disclosures.all():
                questions += [
                    {"question": f"How long have you been diagnosed with {disease.disease_name}?", "reason": "Disease duration helps assess risk."},
                    {"question": f"Are you currently on medication for {disease.disease_name}?", "reason": "Medication indicates disease control."},
                ]

            if family_count > 0:
                questions.append(
                    {"question": "Would you prefer floater or individual coverage for your family?", "reason": "Family presence changes coverage structure options."}
                )

            if cover_amount < 500000:
                questions.append(
                    {"question": "What additional coverage amount would you like to explore?", "reason": "Existing cover appears low compared to standard protection needs."}
                )

            # NEW - Module 7 logging (AI failed, fallback used)
            AIRequestLog.objects.create(
                customer=customer,
                user=request.user,
                log_type='question_suggestion',
                prompt_text=prompt,
                response_text='',
                model_name='gemini-flash-latest',
                status='error',
                error_message=str(e)
            )

            return Response({
                "status": "success",
                "message": "Questions generated via rule-based fallback",
                "data": {
                    "confidence": 0.6,
                    "questions": questions,
                    "source": "rule_based_fallback",
                    "ai_error": str(e)
                }

            }, status=status.HTTP_200_OK)


class SignupView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "status": "success",
                    "message": "User created",
                    "data": {
                        "token": token.key,
                        "user_id": user.id,
                    }
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "message": "Validation failed", "data": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)

            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {
                        "status": "success",
                        "message": "Login successful",
                        "data": {
                            "token": token.key,
                            "user_id": user.id,
                        }
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"status": "error", "message": "Invalid credentials", "data": None},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {"status": "error", "message": "Validation failed", "data": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"http://localhost:8000/api/auth/reset-password/{uid}/{token}/"

            return Response(
                {
                    "status": "success",
                    "message": "Reset link sent",
                    "data": {
                        "reset_link": reset_link,
                    }
                },
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found", "data": None},
                status=status.HTTP_404_NOT_FOUND,
            )


class ResetPasswordView(APIView):
    def post(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            if PasswordResetTokenGenerator().check_token(user, token):
                new_password = request.data.get("new_password")
                user.set_password(new_password)
                user.save()

                return Response(
                    {"status": "success", "message": "Password reset successful", "data": None},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "error", "message": "Invalid token", "data": None},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except:
            return Response(
                {"status": "error", "message": "Invalid request", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MissingInformationView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id, assigned_to=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Customer not found or access denied", "data": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        missing = []

        if customer.premium_budget is None:
            missing.append("Premium Budget")

        if not customer.preferred_hospitals:
            missing.append("Preferred Hospitals")

        insurance_covers = customer.insurance_covers.all()
        if not insurance_covers.exists():
            missing.append("Existing Insurance Cover")
        else:
            for cover in insurance_covers:
                if not cover.claim_history:
                    missing.append("Claim History")
                    break

        for disclosure in customer.medical_disclosures.all():
            if not disclosure.hospitalization_history:
                missing.append("Hospitalization History")
                break

        if not customer.family_members.exists():
            missing.append("Family Information")

        return Response(
            {
                "status": "success",
                "message": "Missing information identified successfully",
                "data": {
                    "customer_id": customer.id,
                    "missing_information": missing,
                }
            },
            status=status.HTTP_200_OK,
        )


# Create Customer - NEW
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_customer(request):
    """
    POST /api/v1/customers/create/
    Create a new customer assigned to current user
    """
    try:
        full_name = request.data.get('full_name')
        age = request.data.get('age')
        gender = request.data.get('gender')
        city = request.data.get('city')
        occupation = request.data.get('occupation')
        annual_income = request.data.get('annual_income')

        if not all([full_name, age, gender, city]):
            return Response({
                "status": "error",
                "message": "full_name, age, gender, city are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.create(
            full_name=full_name,
            age=age,
            gender=gender,
            city=city,
            occupation=occupation or "",
            annual_income=annual_income or 0,
            assigned_to=request.user
        )

        return Response({
            "status": "success",
            "message": "Customer created successfully",
            "data": {
                "id": customer.id,
                "full_name": customer.full_name,
                "age": customer.age,
                "gender": customer.gender,
                "city": customer.city,
                "occupation": customer.occupation,
                "annual_income": str(customer.annual_income),
                "assigned_to": customer.assigned_to.username,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    """return Response(
            {
                "status": "error",
                "message": str(e),
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )"""



"""@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_policies(request):
    try:
        all_covers = ExistingInsuranceCover.objects.filter(
            customer__assigned_to=request.user
        ).select_related("customer")

        policies_data = [
            {
                "provider_name": c.provider_name,
                "policy_type": c.policy_type,
                "coverage_amount": str(c.coverage_amount),
                "customer_name": c.customer.full_name,
            }
            for c in all_covers
        ]

        return Response({
            "status": "success",
            "data": policies_data,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)"""


"""@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_policies(request):
    try:
        all_covers = ExistingInsuranceCover.objects.filter(
            customer__assigned_to=request.user
        ).select_related("customer")

        grouped = {}
        for c in all_covers:
            key = c.policy_number or f"__no_number_{c.id}"
            if key not in grouped:
                grouped[key] = {
                    "policy_number": c.policy_number,
                    "provider_name": c.provider_name,
                    "policy_type": c.policy_type,
                    "customers": [],
                }
            grouped[key]["customers"].append({
                "name": c.customer.full_name,
                "coverage_amount": str(c.coverage_amount),
            })

        policies_data = list(grouped.values())

        return Response({
            "status": "success",
            "data": policies_data,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)"""


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_policies(request):
    """Get all policies for logged-in agent"""
    try:
        """policies = Policy.objects.filter(
            agent=request.user
        ).select_related("customer").order_by('-created_at')"""

        policies = (
                Policy.objects
                .exclude(status='Draft')
                .select_related("customer")
                .order_by('-created_at')
            )

        policies_data = [
            {
                "id": policy.id,
                "policy_number": policy.policy_number or "No Number",
                "policy_type": policy.policy_type,
                "customer_name": policy.customer.full_name,
                "customer_id": policy.customer.id,
                "status": policy.status,
                "premium": str(policy.premium),
                "coverage_amount": str(policy.coverage_amount),
                "term_years": policy.term_years,
                "description": policy.description,
            }
            for policy in policies
        ]

        return Response({
            "status": "success",
            "data": policies_data,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# NEW - Task 3: List policies for a customer


#MODULE 5: QUALIFICATION INSIGHTS
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_detail(request, customer_id):
    """
    GET /api/customer/<customer_id>/
    Fetch customer details by ID
    """
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        return Response(
            {
                "status": "success",
                "message": "Customer details retrieved",
                "data": {
                    "id": customer.id,
                    "full_name": customer.full_name,
                    "age": customer.age,
                    "gender": customer.gender,
                    "city": customer.city,
                    "occupation": customer.occupation,
                    "annual_income": str(customer.annual_income),
                    "premium_budget": str(customer.premium_budget) if customer.premium_budget else None,
                    "preferred_hospitals": customer.preferred_hospitals,
                    "family_members_count": customer.family_members.count(),
                    "medical_disclosures_count": customer.medical_disclosures.count(),
                    "insurance_covers_count": customer.insurance_covers.count(),
                }
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
                "data": None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# NEW - Task 3: List policies for a customer
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_customer_policies(request, customer_id):
    """
    GET /api/customer/<customer_id>/policies/
    List all insurance policies (ExistingInsuranceCover) for a customer
    """
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        policies = customer.insurance_covers.all()

        policies_data = [
            {
                "id": policy.id,
                "provider_name": policy.provider_name,
                "coverage_amount": str(policy.coverage_amount),
                "policy_type": policy.policy_type,
                "claim_history": policy.claim_history,
            }
            for policy in policies
        ]

        return Response(
            {
                "status": "success",
                "message": f"Retrieved {len(policies_data)} policies",
                "data": policies_data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_qualification_insights(request):
    try:
        customer_id = request.data.get("customer_id")

        if not customer_id:
            return Response(
                {
                    "status": "error",
                    "message": "customer_id is required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        engine = QualificationEngine(customer)
        insights_data = engine.evaluate()

        qualification_insight = QualificationInsight.objects.create(
            customer=customer,
            risk_band=insights_data["risk_band"],
            confidence=insights_data["confidence"],
            insights=insights_data["insights"],
            triggered_rules=insights_data["triggered_rules"],
        )

        # NEW - Module 7 logging (rule-based engine, not an LLM call — still logged per Module 7 spec)
        AIRequestLog.objects.create(
            customer=customer,
            user=request.user,
            log_type='qualification_insight',
            prompt_text=f"customer_id={customer_id}",
            response_text=str(insights_data),
            model_name='rule-based-engine',
            status='success'
        )

        return Response(
            {
                "status": "success",
                "message": "Qualification insights generated",
                "data": {
                    "risk_band": qualification_insight.risk_band,
                    "confidence": qualification_insight.confidence,
                    "insights": qualification_insight.insights,
                    "triggered_rules": qualification_insight.triggered_rules,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        # NEW - Module 7 logging (error)
        if 'customer' in locals():
            AIRequestLog.objects.create(
                customer=customer,
                user=request.user,
                log_type='qualification_insight',
                prompt_text=f"customer_id={customer_id}" if 'customer_id' in locals() else '',
                response_text='',
                model_name='rule-based-engine',
                status='error',
                error_message=str(e)
            )

        return Response(
            {
                "status": "error",
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_qualification_insights(request, customer_id):
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        latest_insight = customer.qualification_insights.first()

        if not latest_insight:
            return Response(
                {
                    "status": "error",
                    "message": "No qualification insights found for this customer. Generate one first.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "status": "success",
                "message": "Latest qualification insights retrieved",
                "data": {
                    "risk_band": latest_insight.risk_band,
                    "confidence": latest_insight.confidence,
                    "insights": latest_insight.insights,
                    "triggered_rules": latest_insight.triggered_rules,
                    "created_at": latest_insight.created_at.isoformat(),
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_qualification_insights_history(request, customer_id):
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        insights = customer.qualification_insights.all()

        insights_data = [
            {
                "id": insight.id,
                "risk_band": insight.risk_band,
                "confidence": insight.confidence,
                "insights": insight.insights,
                "triggered_rules": insight.triggered_rules,
                "created_at": insight.created_at.isoformat(),
            }
            for insight in insights
        ]

        return Response(
            {
                "status": "success",
                "message": "Qualification insights history retrieved",
                "data": insights_data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


#MODULE 6: AI CHAT SERVICE

#only accpets POST req
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request): #function to handle AI chat requests
    """
    AI Chat Assistant Endpoint

    POST /api/ai/chat/
    {
        "customer_id": 1,
        "question": "What additional information should I collect?"
    }
    """
    try:
        # Get request data
        customer_id = request.data.get('customer_id')
        advisor_question = request.data.get('question', '').strip() #the .strip removes spaces from beginning/end

        # if customer_id or question is missing, return error
        if not customer_id:
            return Response(
                {"status": "error", "message": "customer_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not advisor_question:
            return Response(
                {"status": "error", "message": "question is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch customer (with security: only own customers)
        customer = get_object_or_404(
            Customer,
            id=customer_id,
            assigned_to=request.user
        )

        # Build customer data for AI
        customer_data = {
            'id': customer.id,
            'name': customer.full_name,
            'age': customer.age,
            'city': customer.city,
            'occupation': customer.occupation,
            'annual_income': customer.annual_income,
            'family_members_count': customer.family_members.count(),
            'family_members': [
                {
                    'relationship': fm.relationship,
                    'age': fm.age,
                    'name': fm.name
                }
                for fm in customer.family_members.all()
            ],
            'medical_disclosures': [
                md.disease_name
                for md in customer.medical_disclosures.all()
            ],
            'insurance_covers': [
                {
                    'provider_name': ic.provider_name,
                    'coverage_amount': ic.coverage_amount,
                    'policy_type': ic.policy_type
                }
                for ic in customer.insurance_covers.all()
            ],
            'total_coverage': sum(
                ic.coverage_amount for ic in customer.insurance_covers.all()
            ),
            'premium_budget': customer.premium_budget
        }

        # Get chat service and generate response
        chat_service = get_chat_service()
        ai_response = chat_service.generate_chat_response(
            customer_data,
            advisor_question
        )

        # NEW - Module 7 logging (success)
        AIRequestLog.objects.create(
            customer=customer,
            user=request.user,
            log_type='chat',
            prompt_text=advisor_question,
            response_text=ai_response.get('answer', ''),
            model_name=ai_response.get('model', 'gemini-flash-latest'),
            status='success'
        )

        # NEW - Module 8 versioning
        latest_version = AIOutputVersion.objects.filter(
            customer=customer,
            output_type='chat'
        ).order_by('-version_number').first()
        next_version = (latest_version.version_number + 1) if latest_version else 1

        AIOutputVersion.objects.create(
            customer=customer,
            output_type='chat',
            version_number=next_version,
            response_json={
                'question': advisor_question,
                'answer': ai_response.get('answer', ''),
                'model': ai_response.get('model', 'gemini-flash-latest')
            },
            model_used=ai_response.get('model', 'gemini-flash-latest')
        )

        # Return response
        return Response(
            {
                "status": ai_response['status'],
                "data": {
                    "answer": ai_response['answer'],
                    "model": ai_response['model'],
                    "question": ai_response['question']
                }
            },
            status=status.HTTP_200_OK
        )

    #if customer doesnt exist or not assigned to the user, return 404
    except Customer.DoesNotExist:
        return Response(
            {
                "status": "error",
                "message": "Customer not found or not assigned to you"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        # NEW - Module 7 logging (error) — only if customer was resolved before failure
        if 'customer' in locals():
            AIRequestLog.objects.create(
                customer=customer,
                user=request.user,
                log_type='chat',
                prompt_text=advisor_question if 'advisor_question' in locals() else '',
                response_text='',
                model_name='gemini-flash-latest',
                status='error',
                error_message=str(e)
            )

        return Response(
            {
                "status": "error",
                "message": "An error occurred while processing your request"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Module 7 - AI Logging
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_logs(request, customer_id):
    """
    GET /api/v1/customers/<customer_id>/ai-logs/
    Retrieve all AI logs for a customer
    """
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )
    except:
        return Response(
            {"status": "error", "message": "Customer not found or access denied"},
            status=status.HTTP_404_NOT_FOUND
        )

    logs = AIRequestLog.objects.filter(customer=customer)
    serializer = AIRequestLogSerializer(logs, many=True)

    return Response({
        "status": "success",
        "message": f"Retrieved {logs.count()} AI logs",
        "data": serializer.data
    }, status=status.HTTP_200_OK)


# Module 8 - AI Output Versioning

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_ai_output_version(request):
    """
    POST /api/v1/ai/output-versions/save/
    Save an AI output version
    """
    try:
        customer_id = request.data.get('customer_id')
        output_type = request.data.get('output_type')
        response_json = request.data.get('response_json')
        model_used = request.data.get('model_used', 'gemini-pro')

        if not all([customer_id, output_type, response_json]):
            return Response({
                "status": "error",
                "message": "customer_id, output_type, response_json are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )

        # Get next version number
        latest_version = AIOutputVersion.objects.filter(
            customer=customer,
            output_type=output_type
        ).order_by('-version_number').first()

        next_version = (latest_version.version_number + 1) if latest_version else 1

        output_version = AIOutputVersion.objects.create(
            customer=customer,
            output_type=output_type,
            version_number=next_version,
            response_json=response_json,
            model_used=model_used
        )

        serializer = AIOutputVersionSerializer(output_version)

        return Response({
            "status": "success",
            "message": "AI output version saved",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_output_versions(request, customer_id):
    """
    GET /api/v1/customers/<customer_id>/ai-output-versions/
    Retrieve all AI output versions for a customer
    """
    try:
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user), pk=customer_id
        )
    except:
        return Response({
            "status": "error",
            "message": "Customer not found or access denied"
        }, status=status.HTTP_404_NOT_FOUND)

    versions = AIOutputVersion.objects.filter(customer=customer)
    serializer = AIOutputVersionSerializer(versions, many=True)

    return Response({
        "status": "success",
        "message": f"Retrieved {versions.count()} AI output versions",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

#login stuff
@login_required(login_url='login')
def customers_list(request):
    customers = Customer.objects.filter(assigned_to=request.user).order_by('-id')
    return render(request, 'customers.html', {'customers': customers, 'customers_count': customers.count()})

@login_required(login_url='login')
def policies_view(request):
    return render(request, 'policies.html')



#added for the dashboard graphs
# ===== DASHBOARD API ENDPOINTS =====
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    WHY: This gets REAL data from your database instead of hardcoded numbers.
    It calculates:
    - Total customers assigned to this advisor
    - Active policies (status = 'Active')
    - Month-over-month growth for both
    """
    try:
        # Get only this advisor's customers (security)
        customers = Customer.objects.filter(assigned_to=request.user)
        
        # 1. TOTAL CUSTOMERS - Count all customers assigned to this user
        total_customers = customers.count()
        
        # 2. ACTIVE POLICIES - Count only policies with status 'Active'
        active_policies = Policy.objects.filter(
            agent=request.user,
            status='Active'
        ).count()
        
        # 3. CUSTOMER GROWTH - Compare last 30 days vs previous 30 days
        from datetime import datetime, timedelta
        today = datetime.now()
        last_month_start = today - timedelta(days=30)
        previous_month_start = today - timedelta(days=60)
        
        customers_last_month = customers.filter(
            created_at__gte=last_month_start
        ).count()
        
        customers_prev_month = customers.filter(
            created_at__gte=previous_month_start,
            created_at__lt=last_month_start
        ).count()
        
        # Calculate percentage growth
        if customers_prev_month > 0:
            customer_growth = round(
                ((customers_last_month - customers_prev_month) / customers_prev_month * 100), 
                1
            )
        else:
            customer_growth = 0
        
        # 4. POLICY GROWTH - Same calculation but for policies
        policies_last_month = Policy.objects.filter(
            agent=request.user,
            created_at__gte=last_month_start
        ).count()
        
        policies_prev_month = Policy.objects.filter(
            agent=request.user,
            created_at__gte=previous_month_start,
            created_at__lt=last_month_start
        ).count()
        
        if policies_prev_month > 0:
            policy_growth = round(
                ((policies_last_month - policies_prev_month) / policies_prev_month * 100),
                1
            )
        else:
            policy_growth = 0
        
        # Return data as JSON
        return Response({
            "status": "success",
            "data": {
                "total_customers": total_customers,
                "customer_growth": customer_growth,
                "active_policies": active_policies,
                "policy_growth": policy_growth,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_customers_data(request):
    """
    WHY: This provides data for the bar chart showing new customers by month.
    Instead of hardcoding [5, 12, 8, 15, 22, 30], it queries the database.
    """
    try:
        from datetime import datetime
        
        # These match your dashboard image: Mar, Apr, May, Jun, Jul, Aug
        months = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
        month_numbers = {'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8}
        
        # Get customers for this advisor
        customers = Customer.objects.filter(assigned_to=request.user)
        
        # Count customers created in each month
        data = []
        current_year = datetime.now().year
        
        for month in months:
            count = customers.filter(
                created_at__month=month_numbers[month],
                created_at__year=current_year
            ).count()
            data.append(count)
        
        return Response({
            "status": "success",
            "data": {
                "labels": months,
                "values": data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def policy_mix_data(request):
    """
    WHY: This provides data for the policy mix pie chart.
    It counts policies of each type (Health, Life, Motor, Term).
    """
    try:
        # These match your dashboard image
        policy_types = ['Health', 'Life', 'Motor', 'Term']
        
        # Count policies of each type for this advisor
        data = []
        for p_type in policy_types:
            count = Policy.objects.filter(
                agent=request.user,
                policy_type=p_type
            ).count()
            data.append(count)
        
        return Response({
            "status": "success",
            "data": {
                "labels": policy_types,
                "values": data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_customers_list_api(request):
    """
    WHY: This populates the "Select a customer" dropdown with real customers.
    Previously it was hardcoded or empty - now it shows actual customers.
    """
    try:
        # Get all customers for this advisor, only need id and name
        customers = Customer.objects.filter(
            assigned_to=request.user
        ).values('id', 'full_name')
        
        return Response({
            "status": "success",
            "data": list(customers)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_detail_api(request, customer_id):
    """
    WHY: This shows customer details when selected from dropdown.
    Previously it showed hardcoded "John Doe" - now it shows real data.
    """
    try:
        # Get the specific customer (ensuring it belongs to this advisor)
        customer = get_object_or_404(
            Customer.objects.filter(assigned_to=request.user),
            id=customer_id
        )
        
        # Get family members count
        family_count = customer.family_members.count()
        
        # Get policies count
        policies_count = customer.policies.filter(agent=request.user).count()
        
        # Get PED (Pre-Existing Diseases) list
        ped_list = [d.disease_name for d in customer.medical_disclosures.all()]
        
        # Get missing information
        missing_info = []
        if customer.premium_budget is None:
            missing_info.append("Premium Budget")
        if not customer.preferred_hospitals:
            missing_info.append("Preferred Hospitals")
        if not customer.insurance_covers.exists():
            missing_info.append("Existing Insurance Cover")
        if not customer.family_members.exists():
            missing_info.append("Family Information")
        
        # Get latest qualification insight if exists
        latest_insight = customer.qualification_insights.first()
        
        return Response({
            "status": "success",
            "data": {
                "id": customer.id,
                "name": customer.full_name,
                "age": customer.age,
                "city": customer.city,
                "family_count": family_count,
                "policies_count": policies_count,
                "ped_list": ped_list,
                "missing_info": missing_info,
                "risk_band": latest_insight.risk_band if latest_insight else "Not assessed",
                "insights": latest_insight.insights if latest_insight else [],
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)