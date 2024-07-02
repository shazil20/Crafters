from .models import *
from rest_framework import serializers


from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [  # List fields explicitly excluding 'groups'
            'id', 'username', 'email', 'password', 'profile_photo', 'profile_photo_url', 'role'
        ]
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password is write-only
        }

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if request is not None and obj.profile_photo and hasattr(obj.profile_photo, 'url'):
            return request.build_absolute_uri(obj.profile_photo.url)
        return None

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'color', 'size', 'price', 'product_picture', 'location']


class CartSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'products']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'user', 'product']

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class FavoritesSerializer(serializers.ModelSerializer):
    # user = CustomUserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, source='product')

    class Meta:
        model = Favorites
        fields = '__all__'

