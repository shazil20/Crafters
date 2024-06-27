from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes
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
    def post(self, request):
        if request.method == 'POST':
            data = request.data
            username = data.get('username')
            password = data.get('password')
            profile_photo = data.get('profile_photo')
            email = data.get('email')
            role = data.get('role', 'user')

            # Create user
            user = CustomUser.objects.create_user(username=username, password=password,
                                                  profile_photo=profile_photo, email=email)

            # Assign role
            user.role = role

            # Save user
            user.save()

            return JsonResponse({'message': 'User created successfully.'})
        else:
            return JsonResponse({'error': 'Method not allowed.'}, status=405)


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
        order = Order.objects.filter(user=user)

        # Serialize the cart items data
        order_data = []
        for item in order:
            image_url = request.build_absolute_uri(
                item.product.product_picture.url) if item.product.product_picture else None
            order_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'price': item.price,
                'quantity': item.quantity,
                'image_url': image_url,
                'status': item.status
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
