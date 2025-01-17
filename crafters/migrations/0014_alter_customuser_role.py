# Generated by Django 5.0.4 on 2024-07-01 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crafters', '0013_alter_customuser_profile_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(blank=True, choices=[('admin', 'Admin'), ('user', 'User')], default='User', max_length=50, null=True),
        ),
    ]
