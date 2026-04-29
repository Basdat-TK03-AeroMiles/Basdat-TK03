from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Manajemen Mitra
    path('mitra/', views.daftar_mitra, name='daftar_mitra'),
    path('mitra/tambah/', views.tambah_mitra, name='tambah_mitra'),
    path('mitra/edit/<str:email_mitra>/', views.edit_mitra, name='edit_mitra'),
    path('mitra/hapus/<str:email_mitra>/', views.hapus_mitra, name='hapus_mitra'),
    
    # Manajemen Hadiah
    path('hadiah/', views.daftar_hadiah, name='daftar_hadiah'),
    path('hadiah/tambah/', views.tambah_hadiah, name='tambah_hadiah'),
    path('hadiah/edit/<str:kode_hadiah>/', views.edit_hadiah, name='edit_hadiah'),
    path('hadiah/hapus/<str:kode_hadiah>/', views.hapus_hadiah, name='hapus_hadiah'),
]