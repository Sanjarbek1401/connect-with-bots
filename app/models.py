from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    passport_series = models.CharField(max_length=2, null=True, blank=True)
    passport_number = models.CharField(max_length=7, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    def verify_passport(self, series, number):
        return (self.passport_series == series and self.passport_number == number)


class InstagramProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    instagram_user_id = models.CharField(max_length=255)  # Instagram foydalanuvchi ID
    username = models.CharField(max_length=255)  # Instagram foydalanuvchi nomi

    def __str__(self):
        return f'Instagram profile for {self.user_profile.user.username}'


class FacebookProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    facebook_user_id = models.CharField(max_length=255)  # Facebook foydalanuvchi ID
    username = models.CharField(max_length=255)  # Facebook foydalanuvchi nomi

    def __str__(self):
        return f'Facebook profile for {self.user_profile.user.username}'


class ChatMessage(models.Model):
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.platform} message from {self.user_profile.user.username}: {self.message_text[:20]}'


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
