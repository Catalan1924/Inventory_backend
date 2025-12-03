from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    SupplierViewSet,
    OrderViewSet,
    LoginView,
    LogoutView,
    RegisterView,
    ProfileView,
    ChangePasswordView,
    UserListView,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-logout"),
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/profile/", ProfileView.as_view(), name="api-profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="api-change-password"),
    path("users/", UserListView.as_view(), name="api-users"),
]
