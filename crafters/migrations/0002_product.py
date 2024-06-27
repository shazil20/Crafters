# Generated by Django 5.0.4 on 2024-05-29 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crafters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('product_picture', models.ImageField(blank=True, null=True, upload_to='product_picture/')),
                ('name', models.TextField(max_length=150)),
                ('price', models.IntegerField()),
                ('size', models.CharField(max_length=150)),
                ('color', models.TextField(max_length=150)),
            ],
        ),
    ]