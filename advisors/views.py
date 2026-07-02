# ===== NEW: imports for Gemini integration =====
import json
import google.generativeai as genai
from django.conf import settings
# ===== NEW END =====

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


# unchanged from before
class CustomerContextView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id, assigned_to=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Customer not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cover = customer.insurance_covers.first()

        context = {
            "customer_summary": {
                "name": customer.full_name,
                "age": customer.age,
                "city": customer.city,
                "family_members": customer.family_members.count(),
                "ped": [d.disease_name for d in customer.medical_disclosures.all()],
                "existing_cover": float(cover.coverage_amount) if cover else 0,
            }
        }
        return Response({"status": "success", **context})


# ===== CHANGED: was pure rule-based, now calls Gemini first, falls back to rules on any failure =====
class QuestionSuggestionsView(APIView):
    def post(self, request):
        customer_id = request.data.get("customer_id")
        try:
            customer = Customer.objects.get(id=customer_id, assigned_to=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Customer not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        diseases = [d.disease_name for d in customer.medical_disclosures.all()]
        cover = customer.insurance_covers.first()
        cover_amount = float(cover.coverage_amount) if cover else 0
        family_count = customer.family_members.count()

        # ===== NEW: build prompt and call Gemini =====
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
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            ai_data = json.loads(raw_text)

            return Response({
                "status": "success",
                "confidence": 0.85,
                "questions": ai_data.get("questions", []),
                "source": "gemini"   # confirms real AI response was used
            })
        # ===== NEW END =====

        # ===== OLD LOGIC: kept as fallback if Gemini call/parsing fails for any reason =====
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
                "confidence": 0.6,
                "questions": questions,
                "source": "rule_based_fallback",  # tells you Gemini failed
                "ai_error": str(e)                # shows why it failed, for debugging
            })
        # ===== OLD LOGIC END =====
# ===== CHANGED END =====


# everything below is unchanged
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
                    "token": token.key,
                    "user_id": user.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
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
                        "token": token.key,
                        "user_id": user.id,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"status": "error", "message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
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
                    "reset_link": reset_link,
                },
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found"},
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
                    {"status": "success", "message": "Password reset successful"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "error", "message": "Invalid token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except:
            return Response(
                {"status": "error", "message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )