from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import datetime


class CustomUser(AbstractUser):
    id = models.AutoField(primary_key=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('user', 'User')], null=True, blank=True)

    class Meta:
        db_table = 'custom_user'

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    product_picture = models.ImageField(upload_to='product_picture/', null=True, blank=True)
    name = models.TextField(max_length=150, blank=False, null=False)
    price = models.IntegerField(blank=False, null=False)
    size = models.CharField(max_length=150, blank=False, null=False)
    color = models.TextField(max_length=150, blank=False, null=False)
    location = models.CharField(max_length=150, blank=False, null=False, default='')

    def __str__(self):
        return f"{self.name} - {self.color} - {self.size} - ${self.price} - ${self.location}"



class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField(blank=True, null=True, default='')
    quantity = models.IntegerField(blank=True, null=True, default='')
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DELIVERED', 'Delivered'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.user} - {self.product} - {self.price} - {self.quantity} - {self.status}"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField(blank=True, null=True, default='')
    quantity = models.IntegerField(blank=True, null=True, default='')
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DELIVERED', 'Delivered'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    type = models.CharField(max_length=10, default='CASH ON DELEIVERY')

    def __str__(self):
        return f"{self.user} - {self.product} - {self.price} - {self.quantity} - {self.status} - {self.type}"


class Contact(models.Model):
    name = models.CharField(max_length=50, blank = True, null= True, default= 'Anonymous')
    subject = models.CharField(max_length=50, blank = True, null= True, default= 'Anonymous')
    email = models.EmailField()
    message = models.CharField(max_length=400, blank = True, null= True, default= 'Anonymous')
    date = models.DateTimeField(auto_now_add=True)