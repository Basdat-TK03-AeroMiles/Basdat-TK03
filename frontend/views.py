from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from functools import wraps
import datetime



def execute_query(query, params=None, fetch=False):

    with connection.cursor() as cursor:
        cursor.execute(query, params) if params else cursor.execute(query)
        if fetch:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    return None


def fetch_one(query, params=None):

    rows = execute_query(query, params, fetch=True)
    return rows[0] if rows else None


def get_member_miles(email):

    row = fetch_one("SELECT award_miles FROM aeromiles.member WHERE email = %s", [email])
    return row['award_miles'] if row else 0



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

        user = fetch_one(
            "SELECT email, password, salutation, first_mid_name, last_name FROM aeromiles.pengguna WHERE email = %s",
            [email]
        )

        if not user or user['password'] != password:
            messages.error(request, 'Email atau password salah!')
            return redirect('login')

        request.session['email'] = email
        request.session['name'] = f"{user['salutation']} {user['first_mid_name']} {user['last_name']}"

        if fetch_one("SELECT email FROM aeromiles.staf WHERE email = %s", [email]):
            request.session['role'] = 'staf'
        elif fetch_one("SELECT email FROM aeromiles.member WHERE email = %s", [email]):
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



@login_required_view
def dashboard_view(request):
    role = request.session.get('role')
    email = request.session.get('email')

    user = fetch_one("""
        SELECT salutation, first_mid_name, last_name, email,
               kewarganegaraan, tanggal_lahir, country_code, mobile_number
        FROM aeromiles.pengguna WHERE email = %s
    """, [email]) or {}

    context = {'user': user, 'role': role, 'name': request.session.get('name')}

    if role == 'member':
        context['member'] = fetch_one("""
            SELECT m.nomor_member, t.nama AS nama_tier, m.total_miles,
                   m.award_miles, m.tanggal_bergabung
            FROM aeromiles.member m
            JOIN aeromiles.tier t ON m.id_tier = t.id_tier
            WHERE m.email = %s
        """, [email]) or {}

        context['recent_transactions'] = execute_query("""
            (SELECT 'Redeem' AS jenis, r.timestamp AS waktu, -h.miles AS miles
             FROM aeromiles.redeem r
             JOIN aeromiles.hadiah h ON r.kode_hadiah = h.kode_hadiah
             WHERE r.email_member = %s)
            UNION ALL
            (SELECT 'Package' AS jenis, mp.timestamp AS waktu, amp.jumlah_award_miles AS miles
             FROM aeromiles.member_award_miles_package mp
             JOIN aeromiles.award_miles_package amp ON mp.id_award_miles_package = amp.id
             WHERE mp.email_member = %s)
            UNION ALL
            (SELECT 'Transfer (Kirim)' AS jenis, t.timestamp AS waktu, -t.jumlah AS miles
             FROM aeromiles.transfer t WHERE t.email_member_1 = %s)
            UNION ALL
            (SELECT 'Transfer (Terima)' AS jenis, t.timestamp AS waktu, t.jumlah AS miles
             FROM aeromiles.transfer t WHERE t.email_member_2 = %s)
            ORDER BY waktu DESC LIMIT 5
        """, [email, email, email, email], fetch=True)

    elif role == 'staf':
        context['staf'] = fetch_one("""
            SELECT s.id_staf, m.nama_maskapai
            FROM aeromiles.staf s
            JOIN aeromiles.maskapai m ON s.kode_maskapai = m.kode_maskapai
            WHERE s.email = %s
        """, [email]) or {}

        context['klaim'] = fetch_one("""
            SELECT
                COUNT(*) FILTER (WHERE status_penerimaan = 'Menunggu') AS menunggu,
                COUNT(*) FILTER (WHERE status_penerimaan = 'Disetujui') AS disetujui,
                COUNT(*) FILTER (WHERE status_penerimaan = 'Ditolak') AS ditolak
            FROM aeromiles.claim_missing_miles
        """) or {'menunggu': 0, 'disetujui': 0, 'ditolak': 0}

    return render(request, 'dashboard.html', context)



@role_required('staf')
def daftar_mitra(request):
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



@role_required('staf')
def daftar_hadiah(request):
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
    email = request.session.get('email')

    if request.method == 'POST':
        kode_hadiah = request.POST.get('kode_hadiah')

        hadiah = fetch_one(
            "SELECT miles, valid_start_date, program_end FROM aeromiles.hadiah WHERE kode_hadiah = %s",
            [kode_hadiah]
        )
        if not hadiah:
            messages.error(request, 'Hadiah tidak ditemukan.')
            return redirect('redeem_hadiah')

        today = datetime.date.today()
        if today < hadiah['valid_start_date'] or today > hadiah['program_end']:
            messages.error(request, 'Hadiah ini sudah tidak dalam periode valid.')
            return redirect('redeem_hadiah')

        miles_dibutuhkan = hadiah['miles']
        award_miles_sekarang = get_member_miles(email)

        if award_miles_sekarang < miles_dibutuhkan:
            messages.error(request, 'Award Miles Anda tidak cukup untuk menukarkan hadiah ini.')
        else:
            try:
                execute_query(
                    "INSERT INTO aeromiles.redeem (email_member, kode_hadiah, timestamp) VALUES (%s, %s, %s)",
                    [email, kode_hadiah, datetime.datetime.now()]
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

    return render(request, 'redeem_hadiah.html', {
        'hadiah_list': hadiah_list,
        'award_miles': get_member_miles(email),
        'riwayat_redeem': riwayat_redeem,
    })



@role_required('member')
def beli_paket_view(request):
    email = request.session.get('email')

    if request.method == 'POST':
        id_paket = request.POST.get('id_paket')

        paket = fetch_one("SELECT jumlah_award_miles FROM aeromiles.award_miles_package WHERE id = %s", [id_paket])
        if not paket:
            messages.error(request, 'Paket tidak ditemukan.')
            return redirect('beli_paket')

        miles_tambahan = paket['jumlah_award_miles']

        try:
            execute_query(
                "INSERT INTO aeromiles.member_award_miles_package (id_award_miles_package, email_member, timestamp) VALUES (%s, %s, %s)",
                [id_paket, email, datetime.datetime.now()]
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
    return render(request, 'beli_paket.html', {'paket_list': paket_list, 'award_miles': get_member_miles(email)})



@role_required('member')
def info_tier_view(request):
    email = request.session.get('email')

    tier_list = execute_query("SELECT * FROM aeromiles.tier ORDER BY minimal_tier_miles ASC", fetch=True)

    member_data = fetch_one("""
        SELECT m.id_tier, m.total_miles, m.award_miles, t.nama AS nama_tier
        FROM aeromiles.member m
        JOIN aeromiles.tier t ON m.id_tier = t.id_tier
        WHERE m.email = %s
    """, [email])

    current_tier_id = member_data['id_tier'] if member_data else None
    total_miles = member_data['total_miles'] if member_data else 0
    nama_tier = member_data['nama_tier'] if member_data else '-'

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



TRANSAKSI_UNION_QUERY = """
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

DELETE_QUERIES = {
    'redeem': "DELETE FROM aeromiles.redeem WHERE email_member = %s AND kode_hadiah = %s AND timestamp = %s",
    'package': "DELETE FROM aeromiles.member_award_miles_package WHERE id_award_miles_package = %s AND email_member = %s AND timestamp = %s",
    'transfer': "DELETE FROM aeromiles.transfer WHERE email_member_1 = %s AND email_member_2 = %s AND timestamp = %s",
}


def _build_filtered_query(base_query, filters):

    wrapped = f"SELECT * FROM ({base_query}) AS all_tx WHERE 1=1"
    params = []

    if filters.get('jenis'):
        wrapped += " AND jenis = %s"
        params.append(filters['jenis'])
    if filters.get('email'):
        wrapped += " AND email_member ILIKE %s"
        params.append(f"%{filters['email']}%")
    if filters.get('dari'):
        wrapped += " AND timestamp >= %s"
        params.append(filters['dari'])
    if filters.get('sampai'):
        wrapped += " AND timestamp <= %s"
        params.append(filters['sampai'] + ' 23:59:59')

    wrapped += " ORDER BY timestamp DESC"
    return wrapped, params or None


def _get_transaksi_stats():

    return {
        'total_miles_beredar': (fetch_one("SELECT COALESCE(SUM(total_miles), 0) AS v FROM aeromiles.member") or {}).get('v', 0),
        'redeem_bulan_ini': (fetch_one("SELECT COUNT(*) AS v FROM aeromiles.redeem WHERE DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)") or {}).get('v', 0),
        'klaim_disetujui': (fetch_one("SELECT COUNT(*) AS v FROM aeromiles.claim_missing_miles WHERE status_penerimaan = 'Disetujui'") or {}).get('v', 0),
    }


def _get_top_members():

    return {
        'top_miles': execute_query("""
            SELECT p.first_mid_name || ' ' || p.last_name AS nama, m.email, m.total_miles
            FROM aeromiles.member m JOIN aeromiles.pengguna p ON m.email = p.email
            ORDER BY m.total_miles DESC LIMIT 5
        """, fetch=True),
        'top_redeem': execute_query("""
            SELECT p.first_mid_name || ' ' || p.last_name AS nama, r.email_member AS email, COUNT(*) AS jumlah
            FROM aeromiles.redeem r JOIN aeromiles.pengguna p ON r.email_member = p.email
            GROUP BY p.first_mid_name, p.last_name, r.email_member ORDER BY jumlah DESC LIMIT 5
        """, fetch=True),
        'top_transfer': execute_query("""
            SELECT p.first_mid_name || ' ' || p.last_name AS nama, t.email_member_1 AS email, COUNT(*) AS jumlah
            FROM aeromiles.transfer t JOIN aeromiles.pengguna p ON t.email_member_1 = p.email
            GROUP BY p.first_mid_name, p.last_name, t.email_member_1 ORDER BY jumlah DESC LIMIT 5
        """, fetch=True),
    }


@role_required('staf')
def laporan_transaksi_view(request):
    filters = {
        'jenis': request.GET.get('jenis', ''),
        'email': request.GET.get('email', ''),
        'dari': request.GET.get('dari', ''),
        'sampai': request.GET.get('sampai', ''),
    }

    query, params = _build_filtered_query(TRANSAKSI_UNION_QUERY, filters)
    transaksi_list = execute_query(query, params, fetch=True)

    return render(request, 'laporan_transaksi.html', {
        'transaksi_list': transaksi_list,
        'stats': _get_transaksi_stats(),
        **_get_top_members(),
        **{f'filter_{k}': v for k, v in filters.items()},
    })


@role_required('staf')
def hapus_transaksi_view(request, jenis, id1, id2, id3):
    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
        return redirect('laporan_transaksi')

    delete_sql = DELETE_QUERIES.get(jenis)
    if not delete_sql:
        messages.error(request, 'Jenis transaksi tidak valid.')
        return redirect('laporan_transaksi')

    try:
        execute_query(delete_sql, [id1, id2, id3])
        messages.success(request, 'Transaksi berhasil dihapus. Penghapusan ini bersifat permanen.')
    except Exception as e:
        messages.error(request, f'Gagal menghapus transaksi: {e}')

    return redirect('laporan_transaksi')
