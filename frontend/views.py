from django.shortcuts import render, redirect
from django.contrib import messages
import datetime

def execute_query(query, params=None, fetch=False):
    if fetch:
        return []
    return None

def login_view(request):
    if request.session.get('role'):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if email == 'admin@aeromiles.com' and password == 'admin123':
            request.session['role'] = 'staf'
            request.session['name'] = 'Mr. Admin Aero'
            request.session['email'] = email
            return redirect('dashboard')
        elif email == 'member@aeromiles.com' and password == 'member123':
            request.session['role'] = 'member'
            request.session['name'] = 'Mr. John William Doe'
            request.session['email'] = email
            return redirect('dashboard')
        else:
            messages.error(request, 'Email atau password salah!')
            return redirect('login')
            
    return render(request, 'login.html')

def register_view(request):
    if request.session.get('role'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        role = request.POST.get('role', 'member')
        email = request.POST.get('email')
        messages.success(request, f'Registrasi berhasil untuk {email} sebagai {role.title()}. Silakan login.')
        return redirect('login')
            
    return render(request, 'register.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def dashboard_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    email = request.session.get('email')
    
    if not request.session.get('role'):
        return redirect('login')

    user_dummy = {
        'salutation': 'Mr.',
        'first_mid_name': 'Jonathan Hans',
        'last_name': 'Emanuelle',
        'email': email,
        'kewarganegaraan': 'Indonesia',
        'tanggal_lahir': datetime.date(2006, 4, 1),
        'country_code': '+62',
        'mobile_number': '81234567890'
    }

    context = {'user': user_dummy, 'role': role, 'name': request.session.get('name')}

    if role == 'member':
        context['member'] = {
            'nomor_member': 'M2406',
            'nama_tier': 'Gold',
            'total_miles': 45000,
            'award_miles': 32000,
            'tanggal_bergabung': datetime.date(2025, 9, 1)
        }
        context['recent_transactions'] = [
            {'jenis': 'Transfer (Kirim)', 'waktu': datetime.datetime(2026, 4, 15, 10, 30), 'miles': -5000},
            {'jenis': 'Redeem', 'waktu': datetime.datetime(2026, 4, 20, 16, 0), 'miles': -3000},
            {'jenis': 'Package', 'waktu': datetime.datetime(2026, 4, 25, 8, 0), 'miles': 10000},
        ]
        
    elif role == 'staf':
        context['staf'] = {
            'id_staf': 'S2406',
            'nama_maskapai': 'Garuda Indonesia'
        }
        context['klaim'] = {
            'menunggu': 2,
            'disetujui': 5,
            'ditolak': 1
        }

    return render(request, 'dashboard.html', context)

def daftar_mitra(request):
    if request.session.get('role') != 'staf': return redirect('dashboard')
    
    mitra_list = [
        {'email_mitra': 'partner@traveloka.com', 'id_penyedia': 1, 'nama_mitra': 'Traveloka Partner', 'tanggal_kerja_sama': datetime.date(2023, 1, 15)},
        {'email_mitra': 'partner@plazapremium.com', 'id_penyedia': 2, 'nama_mitra': 'Plaza Premium', 'tanggal_kerja_sama': datetime.date(2023, 6, 1)},
    ]
    return render(request, 'mitra.html', {'mitra_list': mitra_list})

def tambah_mitra(request):
    if request.method == 'POST':
        messages.success(request, 'Mitra dummy berhasil ditambahkan.')
        return redirect('daftar_mitra')

def edit_mitra(request, email_mitra):
    if request.method == 'POST':
        messages.success(request, 'Mitra dummy berhasil diubah.')
    return redirect('daftar_mitra')

def hapus_mitra(request, email_mitra):
    messages.success(request, 'Mitra dummy berhasil dihapus.')
    return redirect('daftar_mitra')

def daftar_hadiah(request):
    if request.session.get('role') != 'staf': return redirect('dashboard')
    
    hadiah_list = [
        {
            'kode_hadiah': 'RWD-001', 
            'nama': 'Tiket Domestik PP', 
            'nama_penyedia': 'Garuda Indonesia', 
            'miles': 15000, 
            'deskripsi': 'Tiket pulang-pergi rute domestik.',
            'valid_start_date': datetime.date(2024, 1, 1),
            'program_end': datetime.date(2025, 12, 31)
        },
        {
            'kode_hadiah': 'RWD-003', 
            'nama': 'Voucher Hotel', 
            'nama_penyedia': 'Traveloka Partner', 
            'miles': 5000, 
            'deskripsi': 'Voucher menginap hotel.',
            'valid_start_date': datetime.date(2024, 6, 1),
            'program_end': datetime.date(2025, 6, 30)
        },
    ]
    
    penyedia_list = [
        {'id': 1, 'nama_penyedia': 'Traveloka Partner'},
        {'id': 2, 'nama_penyedia': 'Garuda Indonesia'},
    ]
    
    return render(request, 'hadiah.html', {'hadiah_list': hadiah_list, 'penyedia_list': penyedia_list})

def tambah_hadiah(request):
    if request.method == 'POST':
        messages.success(request, 'Hadiah dummy berhasil ditambahkan.')
        return redirect('daftar_hadiah')

def edit_hadiah(request, kode_hadiah):
    if request.method == 'POST':
        messages.success(request, 'Hadiah dummy berhasil diubah.')
    return redirect('daftar_hadiah')

def hapus_hadiah(request, kode_hadiah):
    messages.success(request, 'Hadiah dummy berhasil dihapus.')
    return redirect('daftar_hadiah')


def manajemen_member_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if role != 'staf':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Staf.')
        return redirect('dashboard')
        
    return render(request, 'manajemen_member.html', {'role': role, 'name': name})


def manajemen_identitas_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')
        
    return render(request, 'manajemen_identitas.html', {'role': role, 'name': name})


def form_identitas_view(request):
    if request.method == 'POST':
        messages.success(request, 'Data identitas berhasil disimpan!')
        return redirect('manajemen_identitas')
    return render(request, 'form_identitas.html')


def form_member_view(request):
    if request.method == 'POST':
        messages.success(request, 'Data member berhasil diperbarui!')
        return redirect('manajemen_member')
    return render(request, 'form_member.html')

def pengaturan_profil_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if not role:
        return redirect('login')

    profile_data = {
        'email': 'member@aeromiles.com' if role == 'member' else 'admin@aeromiles.com',
        'salutation': 'Mr.',
        'first_name': 'John William' if role == 'member' else 'Admin',
        'last_name': 'Doe' if role == 'member' else 'Aero',
        'country_code': '+62',
        'phone': '81234567890',
        'nationality': 'Indonesia',
        'birth_date': '1995-01-01',
    }

    if role == 'member':
        profile_data.update({
            'nomor_member': 'M0001',
            'tgl_bergabung': '2024-01-15'
        })
    else:
        profile_data.update({
            'id_staf': 'S001',
            'maskapai': 'GIAA'
        })

    if request.method == 'POST':
        messages.success(request, 'Profil berhasil diperbarui!')
        return redirect('pengaturan_profil')

    return render(request, 'pengaturan_profil.html', {
        'role': role, 
        'name': name, 
        'profile': profile_data
    })

def klaim_miles_view(request):
    role = request.session.get('role')
    if role != 'member':
        return redirect('dashboard')

    klaim_list = [
        {
            'id': 1,
            'maskapai': 'GA',
            'bandara_asal': 'CGK',
            'bandara_tujuan': 'DPS',
            'tanggal_penerbangan': datetime.date(2024, 10, 1),
            'flight_number': 'GA404',
            'kelas_kabin': 'Business',
            'status_penerimaan': 'Disetujui',
            'timestamp': '2024-10-05 18:45:00'
        },
        {
            'id': 2,
            'maskapai': 'SQ',
            'bandara_asal': 'SIN',
            'bandara_tujuan': 'NRT',
            'tanggal_penerbangan': datetime.date(2024, 11, 15),
            'flight_number': 'SQ12',
            'kelas_kabin': 'Economy',
            'status_penerimaan': 'Menunggu',
            'timestamp': '2024-11-20 18:45:00'
        },
    ]

    context = {
        'role': role,
        'name': request.session.get('name'),
        'klaim_list': klaim_list,
        'maskapai_choices': ['GA', 'SQ', 'MH'],
        'bandara_choices': ['CGK', 'SIN', 'DPS', 'NRT'],
        'kelas_choices': ['Economy', 'Business', 'First']
    }
    return render(request, 'klaim_miles.html', context)

def ajukan_klaim(request):
    if request.method == 'POST':
        messages.success(request, 'Klaim berhasil diajukan!')
    return redirect('klaim_miles')

def edit_klaim(request, id):
    if request.method == 'POST':
        messages.success(request, f'Klaim ID {id} berhasil diupdate!')
    return redirect('klaim_miles')

def batalkan_klaim(request, id):
    messages.success(request, f'Klaim ID {id} berhasil dihapus!')
    return redirect('klaim_miles')

def kelola_klaim_staf(request):
    role = request.session.get('role')
    if role != 'staf':
        return redirect('dashboard')

    klaim_staf_list = [
        {
            'id': 1,
            'nama_member': 'John W. Doe',
            'email_member': 'member@aeromiles.com',
            'maskapai': 'GA',
            'rute': 'CGK → DPS',
            'tanggal': '2024-10-01',
            'flight': 'GA404',
            'kelas': 'Business',
            'tanggal_pengajuan': '2024-10-05 18:45:00',
            'status': 'Disetujui'
        },
        {
            'id': 2,
            'nama_member': 'John W. Doe',
            'email_member': 'member@aeromiles.com',
            'maskapai': 'SQ',
            'rute': 'SIN → NRT',
            'tanggal': '2024-11-15',
            'flight': 'SQ12',
            'kelas': 'Economy',
            'tanggal_pengajuan': '2024-11-20 18:45:00',
            'status': 'Menunggu'
        },
        {
            'id': 3,
            'nama_member': 'Jane Smith',
            'email_member': 'jane@example.com',
            'maskapai': 'GA',
            'rute': 'CGK → SUB',
            'tanggal': '2024-12-01',
            'flight': 'GA310',
            'kelas': 'Economy',
            'tanggal_pengajuan': '2024-12-05 18:45:00',
            'status': 'Menunggu'
        }
    ]

    return render(request, 'kelola_klaim_staf.html', {'klaim_list': klaim_staf_list})

def setujui_klaim(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Klaim CLM-00{pk} berhasil disetujui. Miles telah ditambahkan ke member.')
    return redirect('kelola_klaim_staf')

def tolak_klaim(request, pk):
    if request.method == 'POST':
        messages.error(request, f'Klaim CLM-00{pk} telah ditolak.')
    return redirect('kelola_klaim_staf')

def transfer_miles(request):
    riwayat_transfer = [
        {
            'waktu': '2025-01-15 10:30',
            'nama_member': 'Jane Smith',
            'email_member': 'jane@example.com',
            'jumlah': -5000,
            'catatan': 'Hadiah ulang tahun',
            'tipe': 'Kirim'
        },
        {
            'waktu': '2025-02-01 14:00',
            'nama_member': 'Budi A. Santoso',
            'email_member': 'budi@example.com',
            'jumlah': 2000,
            'catatan': '-',
            'tipe': 'Terima'
        }
    ]
    
    context = {
        'riwayat_transfer': riwayat_transfer,
        'award_miles_tersedia': "32,000"
    }
    return render(request, 'transfer_miles.html', context)

def proses_transfer(request):
    if request.method == 'POST':
        email = request.POST.get('email_penerima')
        jumlah = request.POST.get('jumlah_miles')
        
        messages.success(request, f'Berhasil mengirim {jumlah} miles ke {email}!')
        
    return redirect('transfer_miles')

DUMMY_HADIAH_KATALOG = [
    {'kode_hadiah': 'RWD-001', 'nama': 'Tiket Domestik PP', 'nama_penyedia': 'Garuda Indonesia', 'miles': 15000, 'deskripsi': 'Tiket pulang-pergi rute domestik.', 'valid_start_date': datetime.date(2024, 1, 1), 'program_end': datetime.date(2027, 12, 31), 'id_penyedia': 1},
    {'kode_hadiah': 'RWD-002', 'nama': 'Lounge Access', 'nama_penyedia': 'Plaza Premium', 'miles': 3000, 'deskripsi': 'Akses lounge bandara internasional.', 'valid_start_date': datetime.date(2024, 3, 1), 'program_end': datetime.date(2027, 6, 30), 'id_penyedia': 2},
    {'kode_hadiah': 'RWD-003', 'nama': 'Voucher Hotel', 'nama_penyedia': 'Traveloka Partner', 'miles': 5000, 'deskripsi': 'Voucher menginap hotel bintang 4.', 'valid_start_date': datetime.date(2024, 6, 1), 'program_end': datetime.date(2027, 6, 30), 'id_penyedia': 3},
    {'kode_hadiah': 'RWD-004', 'nama': 'Upgrade Kelas', 'nama_penyedia': 'Garuda Indonesia', 'miles': 20000, 'deskripsi': 'Upgrade dari ekonomi ke bisnis.', 'valid_start_date': datetime.date(2024, 1, 1), 'program_end': datetime.date(2027, 12, 31), 'id_penyedia': 1},
]

DUMMY_REDEEM_HISTORY = [
    {'timestamp': datetime.datetime(2026, 4, 20, 16, 0), 'kode_hadiah': 'RWD-002', 'nama_hadiah': 'Lounge Access', 'miles': 3000},
    {'timestamp': datetime.datetime(2026, 4, 28, 9, 45), 'kode_hadiah': 'RWD-003', 'nama_hadiah': 'Voucher Hotel', 'miles': 5000},
]

DUMMY_PAKET = [
    {'id': 'AMP-001', 'jumlah_award_miles': 1000, 'harga_paket': 150000},
    {'id': 'AMP-002', 'jumlah_award_miles': 2500, 'harga_paket': 350000},
    {'id': 'AMP-003', 'jumlah_award_miles': 5000, 'harga_paket': 650000},
    {'id': 'AMP-004', 'jumlah_award_miles': 10000, 'harga_paket': 1200000},
    {'id': 'AMP-005', 'jumlah_award_miles': 25000, 'harga_paket': 2750000},
    {'id': 'AMP-006', 'jumlah_award_miles': 50000, 'harga_paket': 5000000},
]

DUMMY_TIERS = [
    {'id_tier': 'T001', 'nama': 'Blue', 'minimal_frekuensi_terbang': 0, 'minimal_tier_miles': 0},
    {'id_tier': 'T002', 'nama': 'Silver', 'minimal_frekuensi_terbang': 5, 'minimal_tier_miles': 10000},
    {'id_tier': 'T003', 'nama': 'Gold', 'minimal_frekuensi_terbang': 15, 'minimal_tier_miles': 30000},
    {'id_tier': 'T004', 'nama': 'Platinum', 'minimal_frekuensi_terbang': 30, 'minimal_tier_miles': 75000},
]

DUMMY_TRANSAKSI = [
    {'jenis': 'redeem', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 3000, 'timestamp': datetime.datetime(2026, 4, 20, 16, 0), 'id1': 'member@aeromiles.com', 'id2': 'RWD-002', 'id3': '2026-04-20 16:00:00', 'deskripsi': 'Redeem: Lounge Access'},
    {'jenis': 'package', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 10000, 'timestamp': datetime.datetime(2026, 4, 25, 8, 0), 'id1': 'AMP-004', 'id2': 'member@aeromiles.com', 'id3': '2026-04-25 08:00:00', 'deskripsi': 'Beli Paket: AMP-004 (10000 miles)'},
    {'jenis': 'transfer', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 5000, 'timestamp': datetime.datetime(2026, 4, 15, 10, 30), 'id1': 'member@aeromiles.com', 'id2': 'other@aeromiles.com', 'id3': '2026-04-15 10:30:00', 'deskripsi': 'Transfer 5000 miles ke other@aeromiles.com'},
    {'jenis': 'klaim', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 0, 'timestamp': datetime.datetime(2026, 4, 10, 12, 0), 'id1': '1', 'id2': 'member@aeromiles.com', 'id3': '2026-04-10 12:00:00', 'deskripsi': 'Klaim Disetujui: GA-123 (CGK → DPS)'},
]

AWARD_MILES = 32000


def redeem_hadiah_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    if request.method == 'POST':
        kode_hadiah = request.POST.get('kode_hadiah')
        hadiah = next((h for h in DUMMY_HADIAH_KATALOG if h['kode_hadiah'] == kode_hadiah), None)
        if not hadiah:
            messages.error(request, 'Hadiah tidak ditemukan.')
        elif AWARD_MILES < hadiah['miles']:
            messages.error(request, 'Award Miles Anda tidak cukup untuk menukarkan hadiah ini.')
        else:
            messages.success(request, f'Berhasil menukarkan hadiah! {hadiah["miles"]} Miles telah dipotong.')
        return redirect('redeem_hadiah')

    return render(request, 'redeem_hadiah.html', {
        'hadiah_list': [h for h in DUMMY_HADIAH_KATALOG if h['program_end'] >= datetime.date.today()],
        'award_miles': AWARD_MILES,
        'riwayat_redeem': DUMMY_REDEEM_HISTORY,
    })


def beli_paket_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    if request.method == 'POST':
        id_paket = request.POST.get('id_paket')
        paket = next((p for p in DUMMY_PAKET if p['id'] == id_paket), None)
        if not paket:
            messages.error(request, 'Paket tidak ditemukan.')
        else:
            messages.success(request, f'Berhasil membeli paket! {paket["jumlah_award_miles"]} Miles telah ditambahkan ke akun Anda.')
        return redirect('beli_paket')

    return render(request, 'beli_paket.html', {
        'paket_list': DUMMY_PAKET,
        'award_miles': AWARD_MILES,
    })


def info_tier_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    current_tier_id = 'T003'
    total_miles = 45000
    nama_tier = 'Gold'

    next_tier = None
    found = False
    for t in DUMMY_TIERS:
        if found:
            next_tier = t
            break
        if t['id_tier'] == current_tier_id:
            found = True

    miles_to_next = next_tier['minimal_tier_miles'] - total_miles if next_tier else None

    return render(request, 'info_tier.html', {
        'tier_list': DUMMY_TIERS,
        'current_tier_id': current_tier_id,
        'nama_tier': nama_tier,
        'total_miles': total_miles,
        'next_tier': next_tier,
        'miles_to_next': miles_to_next,
    })


def laporan_transaksi_view(request):
    if request.session.get('role') != 'staf':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Staf.')
        return redirect('dashboard')

    filter_jenis = request.GET.get('jenis', '')
    filter_email = request.GET.get('email', '')

    filtered = DUMMY_TRANSAKSI[:]
    if filter_jenis:
        filtered = [t for t in filtered if t['jenis'] == filter_jenis]
    if filter_email:
        filtered = [t for t in filtered if filter_email.lower() in t['email_member'].lower()]

    return render(request, 'laporan_transaksi.html', {
        'transaksi_list': filtered,
        'stats': {'total_miles_beredar': 125000, 'redeem_bulan_ini': 8, 'klaim_disetujui': 5},
        'top_miles': [
            {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'total_miles': 45000},
            {'nama': 'Budi Santoso', 'email': 'budi@mail.com', 'total_miles': 38000},
            {'nama': 'Dewi Lestari', 'email': 'dewi@mail.com', 'total_miles': 22000},
        ],
        'top_redeem': [
            {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'jumlah': 4},
            {'nama': 'Dewi Lestari', 'email': 'dewi@mail.com', 'jumlah': 2},
        ],
        'top_transfer': [
            {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'jumlah': 3},
            {'nama': 'Budi Santoso', 'email': 'budi@mail.com', 'jumlah': 1},
        ],
        'filter_jenis': filter_jenis,
        'filter_email': filter_email,
        'filter_dari': request.GET.get('dari', ''),
        'filter_sampai': request.GET.get('sampai', ''),
    })


def hapus_transaksi_view(request, jenis, id1, id2, id3):
    if request.session.get('role') != 'staf':
        return redirect('dashboard')

    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
    else:
        messages.success(request, 'Transaksi berhasil dihapus. Penghapusan ini bersifat permanen.')
    return redirect('laporan_transaksi')
