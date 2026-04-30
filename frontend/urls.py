from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    path('staf/member/', views.manajemen_member_view, name='manajemen_member'),
    path('member/identitas/', views.manajemen_identitas_view, name='manajemen_identitas'),
    
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

    path('pengaturan-profil/', views.pengaturan_profil_view, name='pengaturan_profil'),
    path('klaim-miles/', views.klaim_miles_view, name='klaim_miles'),
    path('klaim-miles/tambah/', views.ajukan_klaim, name='ajukan_klaim'),
    path('klaim-miles/edit/<int:id>/', views.edit_klaim, name='edit_klaim'),
    path('klaim-miles/hapus/<int:id>/', views.batalkan_klaim, name='batalkan_klaim'),

    path('staf/kelola-klaim/', views.kelola_klaim_staf, name='kelola_klaim_staf'),
    path('staf/klaim/setujui/<int:pk>/', views.setujui_klaim, name='setujui_klaim'),
    path('staf/klaim/tolak/<int:pk>/', views.tolak_klaim, name='tolak_klaim'),

    path('transfer-miles/', views.transfer_miles, name='transfer_miles'),
    path('transfer-miles/proses/', views.proses_transfer, name='proses_transfer'),
]