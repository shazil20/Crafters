from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from jwt.utils import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.shortcuts import render, redirect
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from django.contrib.auth import authenticate
from .models import CustomUser
from django.contrib.auth import logout
from django.http import JsonResponse


# Create your views here.
class CustomUserListCreateAPIView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class CustomUserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class ProductView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class UserLoginAPIView(APIView):

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        print("username:", username)
        print("password:", password)

        user = authenticate(request, username=username, password=password)
        if user is not None:

            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)

            # Get profile photo URL (assuming a `profile_photo` field exists)
            profile_photo_url = None
            if user.profile_photo:
                profile_photo_url = request.build_absolute_uri(user.profile_photo.url)

            return Response({
                'access': str(refresh.access_token),
                'refresh': refresh_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'email': user.email,
                    'profile_photo_url': profile_photo_url
                }
            })
        else:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class UserRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutAPIView(APIView):
    def post(self, request):
        if request.method == 'POST':
            logout(request)
            return JsonResponse({'message': 'User logged out successfully.'})
        else:
            return JsonResponse({'error': 'Method not allowed.'}, status=405)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_order_status(request, user_id):
    try:
        orders = Order.objects.filter(user_id=user_id)
        if not orders.exists():
            return Response({'message': 'Orders not found'}, status=status.HTTP_404_NOT_FOUND)
    except Order.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    status_update = request.data.get('status')
    if status_update in dict(Order.STATUS_CHOICES):
        orders.update(status=status_update)
        return Response({'message': 'Order status updated successfully'})
    else:
        return Response({'message': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


class CheckoutView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Retrieve the logged-in user
        user = request.user

        # Retrieve the cart items associated with the logged-in user
        orders = Order.objects.filter(user=user)

        # Serialize the cart items data
        order_data = []
        for order in orders:
            image_url = request.build_absolute_uri(
                order.product.product_picture.url) if order.product.product_picture else None
            order_data.append({
                'product_id': order.product.id,
                'product_name': order.product.name,
                'price': order.price,
                'quantity': order.quantity,
                'image_url': image_url,
                'status': order.status,
            })

        return JsonResponse({'order_items': order_data})

    def post(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)

        # Create orders from cart items
        for cart_item in cart_items:
            Order.objects.create(
                user=cart_item.user,
                product=cart_item.product,
                price=cart_item.price,
                quantity=cart_item.quantity,
                status=cart_item.status
            )

        # Delete cart items
        cart_items.delete()

        return Response({'message': 'Orders placed successfully'}, status=status.HTTP_201_CREATED)

class UserCartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Retrieve the logged-in user
        user = request.user

        # Retrieve the cart items associated with the logged-in user
        cart_items = Cart.objects.filter(user=user)

        # Serialize the cart items data
        cart_data = []
        for item in cart_items:
            image_url = request.build_absolute_uri(
                item.product.product_picture.url) if item.product.product_picture else None
            cart_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'price': item.price,
                'quantity': item.quantity,
                'image_url': image_url
            })

        return JsonResponse({'cart_items': cart_data})


class ContactViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class AddToCartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, product_id):
        user = get_object_or_404(CustomUser, id=user_id)
        product = get_object_or_404(Product, id=product_id)
        price = request.data.get('price')
        quantity = request.data.get('quantity')
        date =request.data.get('date')

        # Ensure price and quantity are valid integers
        try:
            price = int(price)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid price value'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid quantity value'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the product is already in the cart
        try:
            cart_item = Cart.objects.get(user=user, product=product)
            # Update the existing cart item
            if cart_item.price is None:
                cart_item.price = 0
            cart_item.price += price
            cart_item.quantity += quantity  # Increment the quantity
            cart_item.save()
            return JsonResponse({'message': 'Product updated in cart successfully'})
        except Cart.DoesNotExist:
            # Create the Cart object if it doesn't exist
            Cart.objects.create(user=user, product=product, price=price, quantity=quantity)
            return JsonResponse({'message': 'Product added to cart successfully'})

    def patch(self, request, user_id, product_id):
        user = get_object_or_404(CustomUser, id=user_id)
        product = get_object_or_404(Product, id=product_id)
        action = request.data.get('action')

        # Validate action
        if action not in ['increase', 'decrease']:
            return JsonResponse({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = get_object_or_404(Cart, user=user, product=product)
        unit_price = product.price

        if action == 'increase':
            cart_item.quantity += 1
            cart_item.price += unit_price
        elif action == 'decrease':
            cart_item.quantity -= 1
            cart_item.price -= unit_price


            if cart_item.quantity <= 0:
                cart_item.delete()
                return JsonResponse({'message': 'Product removed from cart successfully'})

        cart_item.save()
        return JsonResponse({'message': f'Product {action}d successfully'})

    def delete(self, request, user_id, product_id):
        user = get_object_or_404(CustomUser, id=user_id)
        product = get_object_or_404(Product, id=product_id)

        # Delete the Cart object if it exists
        cart_item = get_object_or_404(Cart, user=user, product=product)
        cart_item.delete()

        return JsonResponse({'message': 'Product removed from cart successfully'})


class AdminCheckoutViewSet(APIView):
    # Ensure that only admin users can access these endpoints
    permission_classes = [AllowAny]

    def get(self, request):
        # Retrieve all orders
        orders = Order.objects.all()

        # Serialize the order data
        order_data = []
        for order in orders:
            image_url = request.build_absolute_uri(
                order.product.product_picture.url) if order.product.product_picture else None
            order_data.append({
                'order_id': order.id,
                'user_id': order.user.id,
                'user_email': order.user.email,
                'user_name': order.user.username,
                'product_id': order.product.id,
                'product_name': order.product.name,
                'price': order.price,
                'quantity': order.quantity,
                'image_url': image_url,
                'status': order.status,
                'type': order.type
            })

        return JsonResponse({'order_items': order_data}, safe=False)

    def patch(self, request, pk=None):
        # Ensure the user is an admin
        user = self.request.user
        if not hasattr(user, 'role') or user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the specific order by primary key
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        # Deserialize and validate data
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def search_products(request):
    search_query = request.data.get('q', '')
    location_query = request.data.get('location', '')

    if search_query and location_query:
        filtered_products = Product.objects.filter(
            name__icontains=search_query,
            location__icontains=location_query
        )
    elif search_query:
        filtered_products = Product.objects.filter(name__icontains=search_query)
    elif location_query:
        filtered_products = Product.objects.filter(location__icontains=location_query)
    else:
        filtered_products = Product.objects.all()

    serializer = ProductSerializer(filtered_products, many=True)

    # Include absolute image URLs in the serialized data
    for product_data in serializer.data:
        product_id = product_data['id']
        product = Product.objects.get(pk=product_id)  # Fetch the full product object

        # Assuming your image field is named 'image' and media files are stored in MEDIA_ROOT
        if product.product_picture:
            image_url = request.build_absolute_uri(product.product_picture.url)  # Generate absolute URL
            product_data['image_url'] = image_url

    return Response(serializer.data)






from .forms import CustomPasswordResetForm
from django.contrib.auth import get_user_model
from django.views.generic import View
from django.shortcuts import render





UserModel = get_user_model()

class CustomPasswordResetView(View):
    template_name = 'password_reset_form.html'  # Replace with your template path

    def get(self, request):
        form = CustomPasswordResetForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = UserModel.objects.filter(email=email).first()
            if user:
                current_site = get_current_site(request)
                subject = render_to_string('password_reset_subject.txt', {
                    'site_name': current_site.name,
                })
                email_template = render_to_string('password_reset_email.html', {
                    'user': user,
                    'protocol': request.scheme,
                    'domain': current_site.domain,
                    'uidb64': urlsafe_base64_encode(force_bytes(str(user.pk))),
                    'token': default_token_generator.make_token(user),
                    'password_reset_timeout': user.get_password_reset_timeout(),
                })
                email = EmailMessage(
                    subject=f"Reset Your Password on {current_site.name}",
                    body=email_template,
                    from_email=None,  # Set your email address for sending
                    to=[email],
                )

                email.send()
            return render(request, 'password_reset_done.html')  # Replace with your template path
        return render(request, self.template_name, {'form': form})


class CustomPasswordResetConfirmView(View):
    template_name = 'password_reset_confirm.html'  # Replace with your template path

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, UserModel.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user=user)  # Pass the user object to the form
            return render(request, self.template_name, {'form': form})
        return redirect('password_reset_done')  # Replace with your password reset done URL

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, UserModel.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user, request.POST)  # Pass both user and request.POST
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)  # Pass user to initialize the form properly

        return render(request, self.template_name, {'form': form})


class CustomPasswordResetDoneView(View):
    template_name = 'password_reset_done.html'  # Replace with your template path

    def get(self, request):
        return render(request, self.template_name)


class CustomPasswordResetCompleteView(View):
    template_name = 'password_reset_complete.html'  # Replace with your template path

    def get(self, request):
        return render(request, self.template_name)




class FavoriteViewset(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = FavoritesSerializer
    queryset = Favorites.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Favorites.objects.filter(user=user)
        return Favorites.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"detail": "Favorite deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Favorites.DoesNotExist:
            return Response({"detail": "Favorite not found."}, status=status.HTTP_404_NOT_FOUND)
