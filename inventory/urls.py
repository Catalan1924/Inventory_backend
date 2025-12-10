# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProductViewSet,
    SupplierViewSet,
    OrderViewSet,
    ProfileView,
    ChangePasswordView,
    UsersListView,
    health_check,
    whoami,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("users/", UsersListView.as_view(), name="users"),
    path("whoami/", whoami, name="whoami"),
    path("health/", health_check, name="health"),
    path("", include(router.urls)),
]
