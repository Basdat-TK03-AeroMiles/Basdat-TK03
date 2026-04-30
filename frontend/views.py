from django.shortcuts import render, redirect
from django.contrib import messages
import datetime

from django.db import connection

def execute_query(query, params=None, fetch=False):
    with connection.cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    return None

def login_view(request):
    if request.session.get('role'):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = execute_query(
            "SELECT email, password, salutation, first_mid_name, last_name FROM aeromiles.pengguna WHERE email = %s",
            [email], fetch=True
        )
        
        if not user or user[0]['password'] != password:
            messages.error(request, 'Email atau password salah!')
            return redirect('login')
        
        u = user[0]
        full_name = f"{u['salutation']} {u['first_mid_name']} {u['last_name']}"
        request.session['email'] = email
        request.session['name'] = full_name
        
        member = execute_query("SELECT email FROM aeromiles.member WHERE email = %s", [email], fetch=True)
        staf = execute_query("SELECT email FROM aeromiles.staf WHERE email = %s", [email], fetch=True)
        
        if staf:
            request.session['role'] = 'staf'
        elif member:
            request.session['role'] = 'member'
        else:
            messages.error(request, 'Akun tidak terdaftar sebagai Member atau Staf.')
            return redirect('login')
        
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

def dashboard_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    email = request.session.get('email')
    
    if not request.session.get('role'):
        return redirect('login')

    # Data profil umum [cite: 152, 330]
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
        # Data dummy untuk tampilan dashboard Member [cite: 157, 335]
        context['member'] = {
            'nomor_member': 'M2406',
            'nama_tier': 'Gold',
            'total_miles': 45000,
            'award_miles': 32000,
            'tanggal_bergabung': datetime.date(2025, 9, 1)
        }
        # Riwayat 5 transaksi terbaru [cite: 341]
        context['recent_transactions'] = [
            {'jenis': 'Transfer (Kirim)', 'waktu': datetime.datetime(2026, 4, 15, 10, 30), 'miles': -5000},
            {'jenis': 'Redeem', 'waktu': datetime.datetime(2026, 4, 20, 16, 0), 'miles': -3000},
            {'jenis': 'Package', 'waktu': datetime.datetime(2026, 4, 25, 8, 0), 'miles': 10000},
        ]
        
    elif role == 'staf':
        # Data dummy untuk tampilan dashboard Staf [cite: 163, 376]
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
    
    # List dummy mitra sesuai spesifikasi tugas [cite: 165, 191]
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
    
    # List dummy hadiah sesuai spesifikasi tugas [cite: 186, 1104]
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
    return render(request, 'dashboard.html', {'role': role, 'name': name})


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

def redeem_hadiah_view(request):
    role = request.session.get('role')
    email = request.session.get('email')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        kode_hadiah = request.POST.get('kode_hadiah')

        hadiah = execute_query(
            "SELECT miles, valid_start_date, program_end FROM aeromiles.hadiah WHERE kode_hadiah = %s",
            [kode_hadiah], fetch=True
        )
        if not hadiah:
            messages.error(request, 'Hadiah tidak ditemukan.')
            return redirect('redeem_hadiah')
        
        h = hadiah[0]
        today = datetime.date.today()

        if today < h['valid_start_date'] or today > h['program_end']:
            messages.error(request, 'Hadiah ini sudah tidak dalam periode valid.')
            return redirect('redeem_hadiah')
            
        miles_dibutuhkan = h['miles']

        member = execute_query("SELECT award_miles FROM aeromiles.member WHERE email = %s", [email], fetch=True)
        award_miles_sekarang = member[0]['award_miles'] if member else 0
        
        if award_miles_sekarang < miles_dibutuhkan:
            messages.error(request, 'Award Miles Anda tidak cukup untuk menukarkan hadiah ini.')
        else:
            try:
                timestamp_sekarang = datetime.datetime.now()
                execute_query(
                    "INSERT INTO aeromiles.redeem (email_member, kode_hadiah, timestamp) VALUES (%s, %s, %s)",
                    [email, kode_hadiah, timestamp_sekarang]
                )
                execute_query(
                    "UPDATE aeromiles.member SET award_miles = award_miles - %s WHERE email = %s",
                    [miles_dibutuhkan, email]
                )
                messages.success(request, f'Berhasil menukarkan hadiah! {miles_dibutuhkan} Miles telah dipotong.')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {e}')
                
        return redirect('redeem_hadiah')

    hadiah_list = execute_query("""
        SELECT h.*, COALESCE(m.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS nama_penyedia
        FROM aeromiles.hadiah h
        LEFT JOIN aeromiles.maskapai m ON h.id_penyedia = m.id_penyedia
        LEFT JOIN aeromiles.mitra mt ON h.id_penyedia = mt.id_penyedia
        WHERE h.program_end >= CURRENT_DATE
        ORDER BY h.nama
    """, fetch=True)
    
    riwayat_redeem = execute_query("""
        SELECT r.timestamp, h.nama AS nama_hadiah, h.miles, h.kode_hadiah
        FROM aeromiles.redeem r
        JOIN aeromiles.hadiah h ON r.kode_hadiah = h.kode_hadiah
        WHERE r.email_member = %s
        ORDER BY r.timestamp DESC
    """, [email], fetch=True)
    
    member_data = execute_query("SELECT award_miles FROM aeromiles.member WHERE email = %s", [email], fetch=True)
    award_miles = member_data[0]['award_miles'] if member_data else 0
    
    return render(request, 'redeem_hadiah.html', {
        'hadiah_list': hadiah_list, 
        'award_miles': award_miles,
        'riwayat_redeem': riwayat_redeem,
    })

def beli_paket_view(request):
    role = request.session.get('role')
    email = request.session.get('email')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        id_paket = request.POST.get('id_paket')
        
        paket = execute_query("SELECT jumlah_award_miles FROM aeromiles.award_miles_package WHERE id = %s", [id_paket], fetch=True)
        if not paket:
            messages.error(request, 'Paket tidak ditemukan.')
            return redirect('beli_paket')
            
        miles_tambahan = paket[0]['jumlah_award_miles']
        
        try:
            timestamp_sekarang = datetime.datetime.now()
            execute_query(
                "INSERT INTO aeromiles.member_award_miles_package (id_award_miles_package, email_member, timestamp) VALUES (%s, %s, %s)",
                [id_paket, email, timestamp_sekarang]
            )
            execute_query(
                "UPDATE aeromiles.member SET award_miles = award_miles + %s, total_miles = total_miles + %s WHERE email = %s",
                [miles_tambahan, miles_tambahan, email]
            )
            messages.success(request, f'Berhasil membeli paket! {miles_tambahan} Miles telah ditambahkan ke akun Anda.')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {e}')
                
        return redirect('beli_paket')

    paket_list = execute_query("SELECT * FROM aeromiles.award_miles_package ORDER BY harga_paket", fetch=True)
    member_data = execute_query("SELECT award_miles FROM aeromiles.member WHERE email = %s", [email], fetch=True)
    award_miles = member_data[0]['award_miles'] if member_data else 0
    
    return render(request, 'beli_paket.html', {'paket_list': paket_list, 'award_miles': award_miles})

def info_tier_view(request):
    role = request.session.get('role')
    email = request.session.get('email')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')
        
    tier_list = execute_query("SELECT * FROM aeromiles.tier ORDER BY minimal_tier_miles ASC", fetch=True)
    
    member_data = execute_query("""
        SELECT m.id_tier, m.total_miles, m.award_miles, t.nama AS nama_tier
        FROM aeromiles.member m
        JOIN aeromiles.tier t ON m.id_tier = t.id_tier
        WHERE m.email = %s
    """, [email], fetch=True)
    
    current_tier_id = member_data[0]['id_tier'] if member_data else None
    total_miles = member_data[0]['total_miles'] if member_data else 0
    nama_tier = member_data[0]['nama_tier'] if member_data else '-'
    
    next_tier = None
    if current_tier_id and tier_list:
        found_current = False
        for t in tier_list:
            if found_current:
                next_tier = t
                break
            if t['id_tier'] == current_tier_id:
                found_current = True
    
    miles_to_next = next_tier['minimal_tier_miles'] - total_miles if next_tier else None
    
    return render(request, 'info_tier.html', {
        'tier_list': tier_list,
        'current_tier_id': current_tier_id,
        'nama_tier': nama_tier,
        'total_miles': total_miles,
        'next_tier': next_tier,
        'miles_to_next': miles_to_next,
    })

def laporan_transaksi_view(request):
    role = request.session.get('role')
    
    if role != 'staf':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Staf.')
        return redirect('dashboard')
    
    filter_jenis = request.GET.get('jenis', '')
    filter_email = request.GET.get('email', '')
    filter_dari = request.GET.get('dari', '')
    filter_sampai = request.GET.get('sampai', '')
    
    query = """
        SELECT 'redeem' AS jenis, r.email_member, h.miles AS jumlah_miles, r.timestamp,
               r.email_member AS id1, r.kode_hadiah AS id2, r.timestamp::text AS id3,
               CONCAT('Redeem: ', h.nama) AS deskripsi
        FROM aeromiles.redeem r
        JOIN aeromiles.hadiah h ON r.kode_hadiah = h.kode_hadiah
        UNION ALL
        SELECT 'package' AS jenis, mp.email_member, amp.jumlah_award_miles AS jumlah_miles, mp.timestamp,
               mp.id_award_miles_package AS id1, mp.email_member AS id2, mp.timestamp::text AS id3,
               CONCAT('Beli Paket: ', mp.id_award_miles_package, ' (', amp.jumlah_award_miles, ' miles)') AS deskripsi
        FROM aeromiles.member_award_miles_package mp
        JOIN aeromiles.award_miles_package amp ON mp.id_award_miles_package = amp.id
        UNION ALL
        SELECT 'transfer' AS jenis, t.email_member_1 AS email_member, t.jumlah AS jumlah_miles, t.timestamp,
               t.email_member_1 AS id1, t.email_member_2 AS id2, t.timestamp::text AS id3,
               CONCAT('Transfer ', t.jumlah, ' miles dari ', t.email_member_1, ' ke ', t.email_member_2) AS deskripsi
        FROM aeromiles.transfer t
        UNION ALL
        SELECT 'klaim' AS jenis, c.email_member, 0 AS jumlah_miles, c.timestamp,
               c.id::text AS id1, c.email_member AS id2, c.timestamp::text AS id3,
               CONCAT('Klaim Disetujui: ', c.flight_number, ' (', c.bandara_asal, ' → ', c.bandara_tujuan, ')') AS deskripsi
        FROM aeromiles.claim_missing_miles c
        WHERE c.status_penerimaan = 'Disetujui'
    """
    
    wrapped = f"SELECT * FROM ({query}) AS all_tx WHERE 1=1"
    params = []
    
    if filter_jenis:
        wrapped += " AND jenis = %s"
        params.append(filter_jenis)
    if filter_email:
        wrapped += " AND email_member ILIKE %s"
        params.append(f'%{filter_email}%')
    if filter_dari:
        wrapped += " AND timestamp >= %s"
        params.append(filter_dari)
    if filter_sampai:
        wrapped += " AND timestamp <= %s"
        params.append(filter_sampai + ' 23:59:59')
    
    wrapped += " ORDER BY timestamp DESC"
    
    transaksi_list = execute_query(wrapped, params if params else None, fetch=True)
    
    stats = {}
    total_miles_beredar = execute_query("SELECT COALESCE(SUM(total_miles), 0) AS total FROM aeromiles.member", fetch=True)
    stats['total_miles_beredar'] = total_miles_beredar[0]['total'] if total_miles_beredar else 0
    
    redeem_bulan_ini = execute_query("""
        SELECT COUNT(*) AS total FROM aeromiles.redeem 
        WHERE DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)
    """, fetch=True)
    stats['redeem_bulan_ini'] = redeem_bulan_ini[0]['total'] if redeem_bulan_ini else 0
    
    klaim_disetujui = execute_query("""
        SELECT COUNT(*) AS total FROM aeromiles.claim_missing_miles WHERE status_penerimaan = 'Disetujui'
    """, fetch=True)
    stats['klaim_disetujui'] = klaim_disetujui[0]['total'] if klaim_disetujui else 0
    
    top_miles = execute_query("""
        SELECT p.first_mid_name || ' ' || p.last_name AS nama, m.email, m.total_miles
        FROM aeromiles.member m
        JOIN aeromiles.pengguna p ON m.email = p.email
        ORDER BY m.total_miles DESC LIMIT 5
    """, fetch=True)
    
    top_redeem = execute_query("""
        SELECT p.first_mid_name || ' ' || p.last_name AS nama, r.email_member AS email, COUNT(*) AS jumlah
        FROM aeromiles.redeem r
        JOIN aeromiles.pengguna p ON r.email_member = p.email
        GROUP BY p.first_mid_name, p.last_name, r.email_member
        ORDER BY jumlah DESC LIMIT 5
    """, fetch=True)
    
    top_transfer = execute_query("""
        SELECT p.first_mid_name || ' ' || p.last_name AS nama, t.email_member_1 AS email, COUNT(*) AS jumlah
        FROM aeromiles.transfer t
        JOIN aeromiles.pengguna p ON t.email_member_1 = p.email
        GROUP BY p.first_mid_name, p.last_name, t.email_member_1
        ORDER BY jumlah DESC LIMIT 5
    """, fetch=True)
    
    return render(request, 'laporan_transaksi.html', {
        'transaksi_list': transaksi_list,
        'stats': stats,
        'top_miles': top_miles,
        'top_redeem': top_redeem,
        'top_transfer': top_transfer,
        'filter_jenis': filter_jenis,
        'filter_email': filter_email,
        'filter_dari': filter_dari,
        'filter_sampai': filter_sampai,
    })

def hapus_transaksi_view(request, jenis, id1, id2, id3):
    role = request.session.get('role')
    if role != 'staf':
        return redirect('dashboard')
    
    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
        return redirect('laporan_transaksi')
    
    try:
        if jenis == 'redeem':
            execute_query("DELETE FROM aeromiles.redeem WHERE email_member = %s AND kode_hadiah = %s AND timestamp = %s", [id1, id2, id3])
        elif jenis == 'package':
            execute_query("DELETE FROM aeromiles.member_award_miles_package WHERE id_award_miles_package = %s AND email_member = %s AND timestamp = %s", [id1, id2, id3])
        elif jenis == 'transfer':
            execute_query("DELETE FROM aeromiles.transfer WHERE email_member_1 = %s AND email_member_2 = %s AND timestamp = %s", [id1, id2, id3])
        
        messages.success(request, 'Transaksi berhasil dihapus. Penghapusan ini bersifat permanen.')
    except Exception as e:
        messages.error(request, f'Gagal menghapus transaksi: {e}')
        
    return redirect('laporan_transaksi')
