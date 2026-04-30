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
    
    path('member/redeem/', views.redeem_hadiah_view, name='redeem_hadiah'),
    path('member/package/', views.beli_paket_view, name='beli_paket'),
    path('member/tier/', views.info_tier_view, name='info_tier'),

    path('staf/mitra/', views.daftar_mitra, name='daftar_mitra'),
    path('staf/transaksi/', views.laporan_transaksi_view, name='laporan_transaksi'),
    path('staf/transaksi/hapus/<str:jenis>/<path:id1>/<path:id2>/<path:id3>/', views.hapus_transaksi_view, name='hapus_transaksi'),
    path('staf/mitra/tambah/', views.tambah_mitra, name='tambah_mitra'),
    path('staf/mitra/edit/<str:email_mitra>/', views.edit_mitra, name='edit_mitra'),
    path('staf/mitra/hapus/<str:email_mitra>/', views.hapus_mitra, name='hapus_mitra'),

    path('staf/hadiah/', views.daftar_hadiah, name='daftar_hadiah'),
    path('staf/hadiah/tambah/', views.tambah_hadiah, name='tambah_hadiah'),
    path('staf/hadiah/edit/<str:kode_hadiah>/', views.edit_hadiah, name='edit_hadiah'),
    path('staf/hadiah/hapus/<str:kode_hadiah>/', views.hapus_hadiah, name='hapus_hadiah'),
]