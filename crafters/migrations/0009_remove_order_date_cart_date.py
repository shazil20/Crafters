# Generated by Django 5.0.4 on 2024-06-28 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crafters', '0008_product_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='date',
        ),
        migrations.AddField(
            model_name='cart',
            name='date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
