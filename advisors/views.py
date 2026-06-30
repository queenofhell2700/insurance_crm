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


class CustomerContextView(APIView):
    def get(self, request, customer_id):
        # Security Rule: Filter by assigned_to
        customer = Customer.objects.get(id=customer_id, assigned_to=request.user)

        context = {
            "customer_summary": {
                "name": customer.full_name,
                "age": customer.age,
                "city": customer.city,
                "family_members": customer.family_info.count(),
                "ped": [d.disease_name for d in customer.medical_disclosures.all()],
                "existing_cover": customer.insurance_cover.coverage_amount,
            }
        }
        return Response(context)


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
