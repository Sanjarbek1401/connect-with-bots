from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    passport_series = models.CharField(max_length=2)  # 2 harfli passport seriyasi
    passport_number = models.CharField(max_length=7, unique=True)  # 7 raqamli passport

    def __str__(self):
        return f"{self.user.username} Profile"

class ChatMessage(models.Model):
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)  # Platform nomi uchun 10 uzunlik
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
