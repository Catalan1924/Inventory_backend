# inventory/views.py (auth part)

import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

ADMIN_SIGNUP_KEY = os.environ.get("ADMIN_SIGNUP_KEY")


class RegisterView(APIView):
    """
    Registers both normal users and admins.
    - Normal User: no admin_key (or wrong admin_key) -> is_superuser=False, is_staff=False
    - Admin: role="Admin" AND admin_key matches ADMIN_SIGNUP_KEY -> is_superuser=True, is_staff=True
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password")
        requested_role = request.data.get("role", "User")  # "User" or "Admin"
        admin_key = request.data.get("admin_key")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create a normal user first
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # Only upgrade to Admin if the secret key is correct
        if (
            requested_role == "Admin"
            and admin_key
            and ADMIN_SIGNUP_KEY
            and admin_key == ADMIN_SIGNUP_KEY
        ):
            user.is_staff = True
            user.is_superuser = True
            user.save()

        token, _ = Token.objects.get_or_create(user=user)
        role = "Admin" if user.is_superuser else "Staff" if user.is_staff else "User"

        return Response(
            {
                "message": "User registered successfully",
                "token": token.key,
                "username": user.username,
                "role": role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Logs in any user (User/Admin) and returns the correct role.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        role = "Admin" if user.is_superuser else "Staff" if user.is_staff else "User"

        return Response(
            {
                "message": "Login successful",
                "token": token.key,
                "username": user.username,
                "role": role,
            },
            status=status.HTTP_200_OK,
        )
