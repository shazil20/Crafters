from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register(r'products', ProductView)
router.register(r'contact', ContactViewSet)
router.register(r'favorites', FavoriteViewset, basename='favorites')


urlpatterns = [
    # URL patterns generated by router
    *router.urls,
    path('login/', UserLoginAPIView.as_view(), name='user_login'),
    path('register/', UserRegisterAPIView.as_view(), name='user_register'),
    path('logout/', UserLogoutAPIView.as_view(), name='user_logout'),
    path('users/', CustomUserListCreateAPIView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', CustomUserRetrieveUpdateDestroyAPIView.as_view(),
         name='user-detail'),
    path('users/<int:user_id>/orders/status/', update_order_status, name='update_order_status'),
    path('user-cart/', UserCartView.as_view(), name='user_cart'),
    path('add-to-cart/<int:user_id>/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('admin-checkout/', AdminCheckoutViewSet.as_view(), name= 'admin-checkout'),
    path('admin-checkout/<int:pk>/', AdminCheckoutViewSet.as_view(), name='admin-checkout-detail'),
    path('product/search/', search_products, name='search_products_api'),



    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]