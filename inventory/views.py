from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from .models import Product, Supplier, Order
from .serializers import (
    ProductSerializer,
    SupplierSerializer,
    OrderSerializer,
    UserSerializer,
)


# ============================
# PRODUCT / SUPPLIER / ORDER APIs
# ============================

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("name")
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


# ============================
# AUTHENTICATION
# ============================

class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        if user.is_superuser:
            role = "Admin"
        elif user.is_staff:
            role = "Staff"
        else:
            role = "User"

        return Response(
            {
                "token": token.key,
                "username": user.username,
                "role": role,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

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

        # new users are normal users (not staff)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "User registered successfully",
                "token": token.key,
                "username": user.username,
                "role": "User",
            },
            status=status.HTTP_201_CREATED,
        )


# ============================
# PROFILE + PASSWORD
# ============================

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        data = {
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
        }
        return Response(data)

    def put(self, request):
        u = request.user
        u.email = request.data.get("email", u.email)
        u.first_name = request.data.get("first_name", u.first_name)
        u.last_name = request.data.get("last_name", u.last_name)
        u.save()
        return Response({"message": "Profile updated"})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Old and new password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()
        # keep existing token; user stays logged in
        return Response({"message": "Password changed successfully"})


# ============================
# ADMIN USER MANAGEMENT
# ============================

class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("username")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
