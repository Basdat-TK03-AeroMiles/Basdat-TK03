from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('staf/member/', views.manajemen_member_view, name='manajemen_member'),
    path('member/identitas/', views.manajemen_identitas_view, name='manajemen_identitas'),
    path('member/identitas/form/', views.form_identitas_view, name='form_identitas'),
    path('staf/member/form/', views.form_member_view, name='form_member'),
]