from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    passport_series = models.CharField(max_length=10)  # Adjust length if necessary
    passport_number = models.CharField(max_length=10)  # Adjust length if necessary

    def __str__(self):
        return self.user.username


class ChatMessage(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)  # Telegram, Facebook, Instagram
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.platform} message from {self.user_profile.user.username}: {self.message_text[:20]}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
