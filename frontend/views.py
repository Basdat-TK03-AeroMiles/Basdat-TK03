from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
import datetime


DUMMY_USERS = {
    'member@aeromiles.com': {'password': 'pass', 'salutation': 'Mr.', 'first_mid_name': 'Jonathan Hans', 'last_name': 'Emanuelle', 'email': 'member@aeromiles.com', 'kewarganegaraan': 'Indonesia', 'tanggal_lahir': datetime.date(2006, 4, 1), 'country_code': '+62', 'mobile_number': '81234567890', 'role': 'member'},
    'staf@aeromiles.com': {'password': 'pass', 'salutation': 'Ms.', 'first_mid_name': 'Siti', 'last_name': 'Rahayu', 'email': 'staf@aeromiles.com', 'kewarganegaraan': 'Indonesia', 'tanggal_lahir': datetime.date(1995, 8, 12), 'country_code': '+62', 'mobile_number': '81298765432', 'role': 'staf'},
}

DUMMY_MEMBER = {
    'nomor_member': 'M2406', 'nama_tier': 'Gold', 'id_tier': 'T003',
    'total_miles': 45000, 'award_miles': 32000,
    'tanggal_bergabung': datetime.date(2025, 9, 1),
}

DUMMY_STAF = {'id_staf': 'S2406', 'nama_maskapai': 'Garuda Indonesia'}

DUMMY_TIERS = [
    {'id_tier': 'T001', 'nama': 'Blue', 'minimal_frekuensi_terbang': 0, 'minimal_tier_miles': 0},
    {'id_tier': 'T002', 'nama': 'Silver', 'minimal_frekuensi_terbang': 5, 'minimal_tier_miles': 10000},
    {'id_tier': 'T003', 'nama': 'Gold', 'minimal_frekuensi_terbang': 15, 'minimal_tier_miles': 30000},
    {'id_tier': 'T004', 'nama': 'Platinum', 'minimal_frekuensi_terbang': 30, 'minimal_tier_miles': 75000},
]

DUMMY_HADIAH = [
    {'kode_hadiah': 'RWD-001', 'nama': 'Tiket Domestik PP', 'nama_penyedia': 'Garuda Indonesia', 'miles': 15000, 'deskripsi': 'Tiket pulang-pergi rute domestik.', 'valid_start_date': datetime.date(2024, 1, 1), 'program_end': datetime.date(2027, 12, 31), 'id_penyedia': 1},
    {'kode_hadiah': 'RWD-002', 'nama': 'Lounge Access', 'nama_penyedia': 'Plaza Premium', 'miles': 3000, 'deskripsi': 'Akses lounge bandara internasional.', 'valid_start_date': datetime.date(2024, 3, 1), 'program_end': datetime.date(2027, 6, 30), 'id_penyedia': 2},
    {'kode_hadiah': 'RWD-003', 'nama': 'Voucher Hotel', 'nama_penyedia': 'Traveloka Partner', 'miles': 5000, 'deskripsi': 'Voucher menginap hotel bintang 4.', 'valid_start_date': datetime.date(2024, 6, 1), 'program_end': datetime.date(2027, 6, 30), 'id_penyedia': 3},
    {'kode_hadiah': 'RWD-004', 'nama': 'Upgrade Kelas', 'nama_penyedia': 'Garuda Indonesia', 'miles': 20000, 'deskripsi': 'Upgrade dari ekonomi ke bisnis.', 'valid_start_date': datetime.date(2024, 1, 1), 'program_end': datetime.date(2027, 12, 31), 'id_penyedia': 1},
]

DUMMY_PAKET = [
    {'id': 'AMP-001', 'jumlah_award_miles': 1000, 'harga_paket': 150000},
    {'id': 'AMP-002', 'jumlah_award_miles': 2500, 'harga_paket': 350000},
    {'id': 'AMP-003', 'jumlah_award_miles': 5000, 'harga_paket': 650000},
    {'id': 'AMP-004', 'jumlah_award_miles': 10000, 'harga_paket': 1200000},
    {'id': 'AMP-005', 'jumlah_award_miles': 25000, 'harga_paket': 2750000},
    {'id': 'AMP-006', 'jumlah_award_miles': 50000, 'harga_paket': 5000000},
]

DUMMY_RECENT_TX = [
    {'jenis': 'Transfer (Kirim)', 'waktu': datetime.datetime(2026, 4, 15, 10, 30), 'miles': -5000},
    {'jenis': 'Redeem', 'waktu': datetime.datetime(2026, 4, 20, 16, 0), 'miles': -3000},
    {'jenis': 'Package', 'waktu': datetime.datetime(2026, 4, 25, 8, 0), 'miles': 10000},
    {'jenis': 'Transfer (Terima)', 'waktu': datetime.datetime(2026, 4, 27, 14, 15), 'miles': 2000},
    {'jenis': 'Redeem', 'waktu': datetime.datetime(2026, 4, 28, 9, 45), 'miles': -1500},
]

DUMMY_REDEEM_HISTORY = [
    {'timestamp': datetime.datetime(2026, 4, 20, 16, 0), 'kode_hadiah': 'RWD-002', 'nama_hadiah': 'Lounge Access', 'miles': 3000},
    {'timestamp': datetime.datetime(2026, 4, 28, 9, 45), 'kode_hadiah': 'RWD-003', 'nama_hadiah': 'Voucher Hotel', 'miles': 5000},
]

DUMMY_TRANSAKSI = [
    {'jenis': 'redeem', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 3000, 'timestamp': datetime.datetime(2026, 4, 20, 16, 0), 'id1': 'member@aeromiles.com', 'id2': 'RWD-002', 'id3': '2026-04-20 16:00:00', 'deskripsi': 'Redeem: Lounge Access'},
    {'jenis': 'package', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 10000, 'timestamp': datetime.datetime(2026, 4, 25, 8, 0), 'id1': 'AMP-004', 'id2': 'member@aeromiles.com', 'id3': '2026-04-25 08:00:00', 'deskripsi': 'Beli Paket: AMP-004 (10000 miles)'},
    {'jenis': 'transfer', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 5000, 'timestamp': datetime.datetime(2026, 4, 15, 10, 30), 'id1': 'member@aeromiles.com', 'id2': 'other@aeromiles.com', 'id3': '2026-04-15 10:30:00', 'deskripsi': 'Transfer 5000 miles dari member@aeromiles.com ke other@aeromiles.com'},
    {'jenis': 'klaim', 'email_member': 'member@aeromiles.com', 'jumlah_miles': 0, 'timestamp': datetime.datetime(2026, 4, 10, 12, 0), 'id1': '1', 'id2': 'member@aeromiles.com', 'id3': '2026-04-10 12:00:00', 'deskripsi': 'Klaim Disetujui: GA-123 (CGK → DPS)'},
]

DUMMY_KLAIM = [
    {'id': 1, 'email_member': 'member@aeromiles.com', 'maskapai': 'Garuda Indonesia', 'bandara_asal': 'CGK', 'bandara_tujuan': 'DPS', 'tanggal_penerbangan': datetime.date(2026, 3, 15), 'flight_number': 'GA-123', 'nomor_tiket': 'TKT-001', 'kelas_kabin': 'Ekonomi', 'pnr': 'ABC123', 'status_penerimaan': 'Menunggu', 'timestamp': datetime.datetime(2026, 3, 20, 10, 0), 'email_staf': None},
    {'id': 2, 'email_member': 'member@aeromiles.com', 'maskapai': 'Garuda Indonesia', 'bandara_asal': 'SUB', 'bandara_tujuan': 'CGK', 'tanggal_penerbangan': datetime.date(2026, 2, 10), 'flight_number': 'GA-456', 'nomor_tiket': 'TKT-002', 'kelas_kabin': 'Bisnis', 'pnr': 'DEF456', 'status_penerimaan': 'Disetujui', 'timestamp': datetime.datetime(2026, 2, 15, 14, 30), 'email_staf': 'staf@aeromiles.com'},
]

DUMMY_MITRA = [
    {'email_mitra': 'partner@traveloka.com', 'id_penyedia': 1, 'nama_mitra': 'Traveloka Partner', 'tanggal_kerja_sama': datetime.date(2023, 1, 15)},
    {'email_mitra': 'partner@plazapremium.com', 'id_penyedia': 2, 'nama_mitra': 'Plaza Premium', 'tanggal_kerja_sama': datetime.date(2023, 6, 1)},
]

DUMMY_PENYEDIA = [
    {'id': 1, 'nama_penyedia': 'Garuda Indonesia'},
    {'id': 2, 'nama_penyedia': 'Plaza Premium'},
    {'id': 3, 'nama_penyedia': 'Traveloka Partner'},
]

DUMMY_IDENTITAS = [
    {'id': 1, 'jenis_identitas': 'KTP', 'nomor_identitas': '3201234567890001', 'masa_berlaku': datetime.date(2030, 12, 31)},
    {'id': 2, 'jenis_identitas': 'Paspor', 'nomor_identitas': 'A1234567', 'masa_berlaku': datetime.date(2028, 6, 15)},
]


def login_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(required_role):
    role_labels = {'member': 'Member', 'staf': 'Staf'}
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.session.get('role') != required_role:
                messages.error(request, f'Akses Ditolak: Halaman ini khusus untuk {role_labels.get(required_role, required_role)}.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_view(request):
    if request.session.get('role'):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = DUMMY_USERS.get(email)
        if not user or user['password'] != password:
            messages.error(request, 'Email atau password salah!')
            return redirect('login')

        request.session['email'] = email
        request.session['name'] = f"{user['salutation']} {user['first_mid_name']} {user['last_name']}"
        request.session['role'] = user['role']
        return redirect('dashboard')

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


@login_required_view
def dashboard_view(request):
    role = request.session.get('role')
    email = request.session.get('email')
    user = DUMMY_USERS.get(email, {})
    context = {'user': user, 'role': role, 'name': request.session.get('name')}

    if role == 'member':
        context['member'] = DUMMY_MEMBER
        context['recent_transactions'] = DUMMY_RECENT_TX
    elif role == 'staf':
        context['staf'] = DUMMY_STAF
        context['klaim'] = {'menunggu': 2, 'disetujui': 5, 'ditolak': 1}

    return render(request, 'dashboard.html', context)


@role_required('staf')
def daftar_mitra(request):
    return render(request, 'mitra.html', {'mitra_list': DUMMY_MITRA})


def tambah_mitra(request):
    if request.method == 'POST':
        messages.success(request, 'Mitra berhasil ditambahkan.')
    return redirect('daftar_mitra')


def edit_mitra(request, email_mitra):
    if request.method == 'POST':
        messages.success(request, 'Mitra berhasil diubah.')
    return redirect('daftar_mitra')


def hapus_mitra(request, email_mitra):
    messages.success(request, 'Mitra berhasil dihapus.')
    return redirect('daftar_mitra')


@role_required('staf')
def daftar_hadiah(request):
    return render(request, 'hadiah.html', {'hadiah_list': DUMMY_HADIAH, 'penyedia_list': DUMMY_PENYEDIA})


def tambah_hadiah(request):
    if request.method == 'POST':
        messages.success(request, 'Hadiah berhasil ditambahkan.')
    return redirect('daftar_hadiah')


def edit_hadiah(request, kode_hadiah):
    if request.method == 'POST':
        messages.success(request, 'Hadiah berhasil diubah.')
    return redirect('daftar_hadiah')


def hapus_hadiah(request, kode_hadiah):
    messages.success(request, 'Hadiah berhasil dihapus.')
    return redirect('daftar_hadiah')


@role_required('staf')
def manajemen_member_view(request):
    return render(request, 'manajemen_member.html', {
        'role': request.session.get('role'),
        'name': request.session.get('name'),
    })


@role_required('member')
def manajemen_identitas_view(request):
    return render(request, 'manajemen_identitas.html', {
        'role': request.session.get('role'),
        'name': request.session.get('name'),
        'identitas_list': DUMMY_IDENTITAS,
    })


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


@role_required('member')
def redeem_hadiah_view(request):
    if request.method == 'POST':
        kode_hadiah = request.POST.get('kode_hadiah')
        hadiah = next((h for h in DUMMY_HADIAH if h['kode_hadiah'] == kode_hadiah), None)
        if not hadiah:
            messages.error(request, 'Hadiah tidak ditemukan.')
        elif DUMMY_MEMBER['award_miles'] < hadiah['miles']:
            messages.error(request, 'Award Miles Anda tidak cukup untuk menukarkan hadiah ini.')
        else:
            messages.success(request, f'Berhasil menukarkan hadiah! {hadiah["miles"]} Miles telah dipotong.')
        return redirect('redeem_hadiah')

    return render(request, 'redeem_hadiah.html', {
        'hadiah_list': [h for h in DUMMY_HADIAH if h['program_end'] >= datetime.date.today()],
        'award_miles': DUMMY_MEMBER['award_miles'],
        'riwayat_redeem': DUMMY_REDEEM_HISTORY,
    })


@role_required('member')
def beli_paket_view(request):
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
        'award_miles': DUMMY_MEMBER['award_miles'],
    })


@role_required('member')
def info_tier_view(request):
    current_tier_id = DUMMY_MEMBER['id_tier']
    total_miles = DUMMY_MEMBER['total_miles']
    nama_tier = DUMMY_MEMBER['nama_tier']

    next_tier = None
    found_current = False
    for t in DUMMY_TIERS:
        if found_current:
            next_tier = t
            break
        if t['id_tier'] == current_tier_id:
            found_current = True

    miles_to_next = next_tier['minimal_tier_miles'] - total_miles if next_tier else None

    return render(request, 'info_tier.html', {
        'tier_list': DUMMY_TIERS,
        'current_tier_id': current_tier_id,
        'nama_tier': nama_tier,
        'total_miles': total_miles,
        'next_tier': next_tier,
        'miles_to_next': miles_to_next,
    })


@role_required('staf')
def laporan_transaksi_view(request):
    filter_jenis = request.GET.get('jenis', '')
    filter_email = request.GET.get('email', '')

    filtered = DUMMY_TRANSAKSI[:]
    if filter_jenis:
        filtered = [t for t in filtered if t['jenis'] == filter_jenis]
    if filter_email:
        filtered = [t for t in filtered if filter_email.lower() in t['email_member'].lower()]

    stats = {
        'total_miles_beredar': 125000,
        'redeem_bulan_ini': 8,
        'klaim_disetujui': 5,
    }

    top_miles = [
        {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'total_miles': 45000},
        {'nama': 'Budi Santoso', 'email': 'budi@mail.com', 'total_miles': 38000},
        {'nama': 'Dewi Lestari', 'email': 'dewi@mail.com', 'total_miles': 22000},
    ]
    top_redeem = [
        {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'jumlah': 4},
        {'nama': 'Dewi Lestari', 'email': 'dewi@mail.com', 'jumlah': 2},
    ]
    top_transfer = [
        {'nama': 'Jonathan Emanuelle', 'email': 'member@aeromiles.com', 'jumlah': 3},
        {'nama': 'Budi Santoso', 'email': 'budi@mail.com', 'jumlah': 1},
    ]

    return render(request, 'laporan_transaksi.html', {
        'transaksi_list': filtered,
        'stats': stats,
        'top_miles': top_miles,
        'top_redeem': top_redeem,
        'top_transfer': top_transfer,
        'filter_jenis': filter_jenis,
        'filter_email': filter_email,
        'filter_dari': request.GET.get('dari', ''),
        'filter_sampai': request.GET.get('sampai', ''),
    })


@role_required('staf')
def hapus_transaksi_view(request, jenis, id1, id2, id3):
    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
    else:
        messages.success(request, 'Transaksi berhasil dihapus.')
    return redirect('laporan_transaksi')


@login_required_view
def pengaturan_profil_view(request):
    email = request.session.get('email')
    user = DUMMY_USERS.get(email, {})
    if request.method == 'POST':
        messages.success(request, 'Profil berhasil diperbarui!')
        return redirect('pengaturan_profil')
    return render(request, 'pengaturan_profil.html', {
        'user': user,
        'role': request.session.get('role'),
    })


@role_required('member')
def klaim_miles_view(request):
    return render(request, 'klaim_miles.html', {
        'klaim_list': DUMMY_KLAIM,
    })


@role_required('member')
def ajukan_klaim(request):
    if request.method == 'POST':
        messages.success(request, 'Klaim berhasil diajukan! Menunggu persetujuan staf.')
    return redirect('klaim_miles')


@role_required('member')
def edit_klaim(request, id):
    if request.method == 'POST':
        messages.success(request, 'Klaim berhasil diperbarui.')
    return redirect('klaim_miles')


@role_required('member')
def batalkan_klaim(request, id):
    messages.success(request, 'Klaim berhasil dibatalkan.')
    return redirect('klaim_miles')


@role_required('staf')
def kelola_klaim_staf(request):
    return render(request, 'kelola_klaim_staf.html', {
        'klaim_list': DUMMY_KLAIM,
    })


@role_required('staf')
def setujui_klaim(request, pk):
    messages.success(request, f'Klaim #{pk} berhasil disetujui.')
    return redirect('kelola_klaim_staf')


@role_required('staf')
def tolak_klaim(request, pk):
    messages.success(request, f'Klaim #{pk} berhasil ditolak.')
    return redirect('kelola_klaim_staf')


@role_required('member')
def transfer_miles(request):
    return render(request, 'transfer_miles.html', {
        'award_miles': DUMMY_MEMBER['award_miles'],
    })


@role_required('member')
def proses_transfer(request):
    if request.method == 'POST':
        email_tujuan = request.POST.get('email_tujuan', '')
        jumlah = request.POST.get('jumlah', 0)
        messages.success(request, f'Berhasil mentransfer {jumlah} miles ke {email_tujuan}.')
    return redirect('transfer_miles')
