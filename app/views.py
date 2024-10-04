from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm, UserProfileForm
from django.contrib import messages
from .models import UserProfile
from django.db import IntegrityError
from .models import ChatMessage
from django.contrib.admin.views.decorators import staff_member_required



def index(request):
    user_name = request.user.username if request.user.is_authenticated else "Mehmon"
    context = {'user_name': user_name}
    return render(request, 'app/index.html', context)


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            passport_number = profile_form.cleaned_data['passport_number']
            if UserProfile.objects.filter(passport_number=passport_number).exists():
                messages.error(request, "Bu passport raqami allaqachon ro'yxatdan o'tgan.")
            else:
                try:
                    user = user_form.save()
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    user.is_active = True
                    profile.save()
                    login(request, user)
                    messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz.")
                    return redirect('index')
                except IntegrityError as e:
                    messages.error(request, "Xatolik: " + str(e))
                except Exception as e:
                    messages.error(request, f"Ro'yxatdan o'tishda xatolik: {str(e)}")
        else:
            messages.error(request, "Ro'yxatdan o'tish formasi noto'g'ri to'ldirilgan.")
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()

    return render(request, 'app/register.html', {'user_form': user_form, 'profile_form': profile_form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Muvaffaqiyatli kirish amalga oshirildi.')
                return redirect('index')
            else:
                messages.error(request, 'Noto\'g\'ri foydalanuvchi nomi yoki parol.')
        except Exception as e:
            # Kirish jarayonidagi umumiy xatolarni qo'lga olish
            messages.error(request, f"Kirish jarayonida xatolik yuz berdi: {str(e)}")

    return render(request, 'app/login.html')


def logout_confirm(request):
    if request.method == 'POST':
        logout(request)
        return redirect('goodbye')
    return render(request, 'app/logout_confirm.html')


def goodbye_view(request):
    return render(request, 'app/goodbye.html')


@staff_member_required()
def dashboard_view(request):
    chat_messages = ChatMessage.objects.all()  # Barcha yozishmalarni olish
    return render(request, 'admin/dashboard.html', {'chat_messages': chat_messages})
