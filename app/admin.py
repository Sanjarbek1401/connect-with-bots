from django.contrib import admin
from django.urls import path  # Django URL yo'nalishlarini import qilish
from django.shortcuts import render
from .models import UserProfile, ChatMessage

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'platform', 'message_text', 'timestamp')
    search_fields = ('message_text',)
    list_filter = ('platform',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'passport_series', 'passport_number')
    search_fields = ('user__username',)

# Register models
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)

# Admin paneli sarlavhalarini o'rnating
admin.site.site_header = "Admin Paneli"
admin.site.site_title = "Admin Paneli"
admin.site.index_title = "Dashboard"
