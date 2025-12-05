# inventory/views.py
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes

from .models import Product, Supplier, Order
from .serializers import (
    ProductSerializer,
    SupplierSerializer,
    OrderSerializer,
    UserSerializer,
)


# ------------------------
# AUTHENTICATION VIEWS
# ------------------------

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

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

        user = User.objects.create_user(username=username, email=email, password=password)
        token, _ = Token.objects.get_or_create(user=user)

        role = "Admin" if user.is_superuser else ("Staff" if user.is_staff else "User")

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
        role = "Admin" if user.is_superuser else ("Staff" if user.is_staff else "User")

        return Response(
            {"message": "Login successful", "token": token.key, "username": user.username, "role": role},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Delete token(s) for the current user to log them out
        Token.objects.filter(user=request.user).delete()
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


# ------------------------
# PROFILE + USERS
# ------------------------

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
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({"error": "New password required"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        # Invalidate tokens so user must re-login (optional)
        Token.objects.filter(user=user).delete()
        return Response({"message": "Password changed. Please login again."})


class UsersListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


# ------------------------
# API VIEWSETS
# ------------------------

class ProductViewSet(viewsets.ModelViewSet):
    """
    routes: /products/
    """
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Example of a simple custom action (optional)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def adjust_stock(self, request, pk=None):
        """POST /products/{id}/adjust_stock/ { amount: 5 }"""
        product = self.get_object()
        try:
            amt = int(request.data.get("amount", 0))
        except (ValueError, TypeError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)
        product.stock = max(0, product.stock + amt)
        product.save()
        return Response(self.get_serializer(product).data)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("id")
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Optionally restrict create so product exist and quantity positive
    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")
        if not product_id or not quantity:
            return Response({"error": "product_id and quantity required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError()
        except Exception:
            return Response({"error": "quantity must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)
