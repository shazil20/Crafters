# Generated by Django 5.0.4 on 2024-06-13 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crafters', '0004_product_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='type',
            field=models.CharField(default='CASH ON DELEIVERY', max_length=10),
        ),
    ]
