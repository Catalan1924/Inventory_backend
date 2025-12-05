# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, LogoutView, ProfileView, ChangePasswordView, UsersListView, ProductViewSet, SupplierViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"suppliers", SupplierViewSet)
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/profile/", ProfileView.as_view()),
    path("auth/change-password/", ChangePasswordView.as_view()),
    path("users/", UsersListView.as_view()),  # admin-only
    path("", include(router.urls)),
]
