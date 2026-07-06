# new imports for Gemini integration
import json
import google.generativeai as genai
from django.conf import settings

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import Customer
from .serializers import UserSerializer, LoginSerializer


#changed into the status, msg, 
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
            #here, its returning a detailed description of the customer data, earlier it was a reset link
            "data": {
                "name": customer.full_name,
                "age": customer.age,
                "city": customer.city,
                "family_members": customer.family_members.count(),
                "ped": [d.disease_name for d in customer.medical_disclosures.all()],
                "existing_cover": float(cover.coverage_amount) if cover else 0,
            }
        })


#confidence/questions/source/ai_error is now nested under "data"
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

    #prompt to gemini api
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
            #model = genai.GenerativeModel("gemini-2.0-flash")
            #model = genai.GenerativeModel("gemini-1.5-flash")
            model = genai.GenerativeModel("gemini-flash-latest") 
            response = model.generate_content(prompt)

            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            ai_data = json.loads(raw_text)

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


#token/user_id nested under "data"
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



#token/user_id nested under "data"
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
# ===== CHANGED END =====


#reset link is nested under data
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
#end of change


#here we have nested everything instead of letting it be loose
# also made sure that the format stays the same for evrything
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

#Module 4 - Missing Information Detection
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
# ===== END Module 4 =====