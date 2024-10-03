from django.urls import path
from .views import register, user_login,index,logout_confirm,goodbye_view,dashboard_view

urlpatterns = [
    path('',index,name='index'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', logout_confirm, name='logout'),
    path('goodbye/', goodbye_view, name='goodbye'),
    path('admin/dashboard/', dashboard_view, name='dashboard'),


]

