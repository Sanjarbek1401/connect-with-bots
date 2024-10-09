from django.contrib import admin
from .models import UserProfile, ChatMessage, InstagramProfile

class ChatMessageInline(admin.TabularInline):  # Inline admin interfeysini yaratish
    model = ChatMessage
    extra = 0  # Qo'shimcha bo'sh yozuvlar soni

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'platform', 'message_text', 'timestamp')
    search_fields = ('message_text', 'user_profile__user__username')
    list_filter = ('platform',)
    ordering = ('-timestamp',)  # Oxirgi yozishmalarni birinchi navbatda ko'rsatish

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'passport_series', 'passport_number', 'is_verified')  # is_verified ni qo'shishingiz mumkin
    search_fields = ('user__username',)
    inlines = [ChatMessageInline]  # Yozishmalarni inline tarzda ko'rsatish

class InstagramProfileAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'username', 'instagram_user_id')
    search_fields = ('username',)

# Register models
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(InstagramProfile, InstagramProfileAdmin)

# Admin paneli sarlavhalarini o'rnating
admin.site.site_header = "Admin Paneli"
admin.site.site_title = "Admin Paneli"
admin.site.index_title = "Dashboard"
