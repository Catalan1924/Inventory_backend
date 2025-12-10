import os

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product, Supplier, Order
from .serializers import (
    ProductSerializer,
    SupplierSerializer,
    OrderSerializer,
    UserSerializer,
)

User = get_user_model()

# Read the admin signup key from settings/env
ADMIN_SIGNUP_KEY = getattr(settings, "ADMIN_SIGNUP_KEY", "") or os.environ.get(
    "ADMIN_SIGNUP_KEY", ""
)


def get_user_role(user: User) -> str:
    """
    Helper to map Django flags to a simple role string.
    """
    if user.is_superuser:
        return "Admin"
    if user.is_staff:
        return "Staff"
    return "User"


# -------------------------------------------------------------------
# AUTH VIEWS
# -------------------------------------------------------------------


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        requested_role = request.data.get("role", "User")
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

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # --- ADMIN / STAFF PROMOTION LOGIC ---
        # Only if they REQUEST Admin AND provide the correct ADMIN_SIGNUP_KEY.
        # Otherwise they stay a normal User.
        if requested_role == "Admin":
            if ADMIN_SIGNUP_KEY and admin_key == ADMIN_SIGNUP_KEY:
                user.is_staff = True
                user.is_superuser = True
                user.save()
            else:
                # optional: you can also return 400 here, but we just create a normal user
                pass

        token, _ = Token.objects.get_or_create(user=user)
        role = get_user_role(user)

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
        role = get_user_role(user)

        return Response(
            {
                "message": "Login successful",
                "token": token.key,
                "username": user.username,
                "role": role,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Simple token logout: delete the current auth token.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Token.DoesNotExist:
            pass
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        return Response(data)

    def put(self, request):
        user = request.user
        user.email = request.data.get("email", user.email)
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.save()
        return Response({"message": "Profile updated"})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not request.user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password:
            return Response(
                {"error": "New password is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()
        return Response({"message": "Password changed"})


class UsersListView(APIView):
    """
    Only Admins can view all users.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "You are not allowed to view users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        users = User.objects.all().order_by("-date_joined")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health_check(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def whoami(request):
    user = request.user
    return Response(
        {
            "username": user.username,
            "role": get_user_role(user),
        }
    )


# -------------------------------------------------------------------
# VIEWSETS FOR PRODUCTS, SUPPLIERS, ORDERS
# (use your existing logic if you already had these – here is a basic version)
# -------------------------------------------------------------------


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("name")
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("supplier").all().order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects.select_related("product")
        .all()
        .order_by("-created_at")
    )
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
