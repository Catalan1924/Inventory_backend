import os

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from django.db.models import Sum
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

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

# Strip spaces to avoid mismatch because of trailing spaces in env
ADMIN_SIGNUP_KEY = (os.environ.get("ADMIN_SIGNUP_KEY") or "").strip()


def _get_role_from_user(user: User) -> str:
    """Return a simple string role for the frontend."""
    if user.is_superuser:
        return "Admin"
    if user.is_staff:
        return "Staff"
    return "User"


# -------------------------------------------------------------------
# AUTH VIEWS
# -------------------------------------------------------------------

class RegisterView(APIView):
    """
    Register a new user.

    - Normal user: send username, password, (optional) email.
    - Admin: additionally send role="Admin" and admin_key=<correct key>.

    If role="Admin" is requested but admin_key is wrong,
    return 403 with an error instead of silently creating a normal user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email", "")
        password = request.data.get("password")
        requested_role = request.data.get("role", "User")
        admin_key = (request.data.get("admin_key") or "").strip()

        # Basic validation
        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize role
        requested_role = requested_role or "User"
        if requested_role not in ("Admin", "Staff", "User"):
            requested_role = "User"

        # If they are asking for Admin, validate the admin key
        if requested_role == "Admin":
            if not ADMIN_SIGNUP_KEY:
                # Backend misconfigured – make it very clear
                return Response(
                    {
                        "error": (
                            "Server is not configured with ADMIN_SIGNUP_KEY. "
                            "Admin registration is disabled."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if not admin_key:
                return Response(
                    {"error": "Admin key is required to create an admin account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if admin_key != ADMIN_SIGNUP_KEY:
                return Response(
                    {"error": "Invalid admin key. Account was not created."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)

        # Apply role flags
        if requested_role == "Admin":
            user.is_staff = True
            user.is_superuser = True
        elif requested_role == "Staff":
            user.is_staff = True
        user.save()

        # Auth token
        token, _ = Token.objects.get_or_create(user=user)
        role = _get_role_from_user(user)

        return Response(
            {
                "message": "User registered successfully.",
                "token": token.key,
                "username": user.username,
                "role": role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Login with username + password.
    Returns token, username and role ("Admin", "Staff", "User").
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        role = _get_role_from_user(user)

        return Response(
            {
                "message": "Login successful.",
                "token": token.key,
                "username": user.username,
                "role": role,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Simple token logout: deletes the current token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Token.DoesNotExist:
            pass
        return Response({"message": "Logged out successfully."})


# -------------------------------------------------------------------
# PROFILE / PASSWORD
# -------------------------------------------------------------------

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        user.email = request.data.get("email", user.email)
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.save()
        return Response({"message": "Profile updated."})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Old password and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."})


# -------------------------------------------------------------------
# USERS LIST (ADMIN ONLY)
# -------------------------------------------------------------------

class UsersListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


# -------------------------------------------------------------------
# VIEWSETS (Products, Suppliers, Orders)
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
    queryset = Order.objects.select_related("product").all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


# -------------------------------------------------------------------
# MISC ENDPOINTS
# -------------------------------------------------------------------

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
            "email": user.email,
            "role": _get_role_from_user(user),
        }
    )
