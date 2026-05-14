from django.shortcuts import render, redirect
from django.contrib import messages
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Fungsi untuk membuka koneksi ke Supabase
def get_db_connection():
    return psycopg2.connect(
        host="aws-1-ap-northeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.bragfwhkwwwulxfdsiqm",
        password="Nainggolan123",
        port="6543",
        options="-c search_path=aeromiles"
    )

# Fungsi utama untuk menjalankan query SQL
def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    # RealDictCursor agar hasil fetch berbentuk dictionary (mirip JSON), lebih mudah dibaca di template HTML
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit() # Commit untuk operasi INSERT, UPDATE, DELETE
            return None
    except Exception as e:
        conn.rollback() # Batalkan jika ada error
        print(f"Database Error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def landing_view(request):
    if request.session.get('role'):
        return redirect('dashboard')
    return render(request, 'landing.html')

def login_view(request):
    # Jika sudah login, langsung lempar ke dashboard
    if request.session.get('role'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # 1. Cek kredensial dengan memanggil Stored Procedure di Supabase
            # SP ini akan otomatis melemparkan (RAISE EXCEPTION) jika email/pass salah
            query_user = "SELECT * FROM verify_login(%s, %s)"
            user_data = execute_query(query_user, [email, password], fetch=True)
            
            # Jika tidak ada exception, artinya login berhasil
            if user_data:
                user = user_data[0]
                
                # 2. Tentukan Role dengan mengecek tabel MEMBER dan STAF
                cek_member = execute_query("SELECT email FROM member WHERE email = %s", [email], fetch=True)
                
                if cek_member:
                    role = 'member'
                else:
                    cek_staf = execute_query("SELECT email FROM staf WHERE email = %s", [email], fetch=True)
                    if cek_staf:
                        role = 'staf'
                    else:
                        messages.error(request, 'Akun ditemukan, tetapi tidak terdaftar sebagai Member maupun Staf.')
                        return redirect('login')
                        
                # 3. Simpan data penting ke Session Django
                request.session['role'] = role
                request.session['email'] = user['email']
                request.session['name'] = f"{user['salutation']} {user['first_mid_name']} {user['last_name']}".strip()
                
                return redirect('dashboard')
                
        except Exception as e:
            # Mengambil dan memotong string error bawaan psycopg2 
            # agar hanya memunculkan pesan "Email atau password salah, silakan coba lagi." dari Supabase
            error_msg = str(e).split('\n')[0].replace('P0001: ', '').strip()
            messages.error(request, error_msg)
            return redirect('login')
            
    return render(request, 'login.html')

def register_view(request):
    if request.session.get('role'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        role = request.POST.get('role', 'member')
        email = request.POST.get('email')
        password = request.POST.get('password')
        salutation = request.POST.get('salutation')
        first_mid_name = request.POST.get('first_mid_name')
        last_name = request.POST.get('last_name')
        country_code = request.POST.get('country_code')
        mobile_number = request.POST.get('mobile_number')
        tanggal_lahir = request.POST.get('tanggal_lahir')
        kewarganegaraan = request.POST.get('kewarganegaraan')
        
        try:
            if role == 'member':
                query_reg = """
                    WITH new_user AS (
                        INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING email
                    )
                    INSERT INTO member (email, tanggal_bergabung, id_tier, award_miles, total_miles) 
                    VALUES ((SELECT email FROM new_user), CURRENT_DATE, 'T01', 0, 0)
                """
                params = [email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan]
                execute_query(query_reg, params)
                
            elif role == 'staf':
                kode_maskapai = request.POST.get('kode_maskapai')
                query_reg = """
                    WITH new_user AS (
                        INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING email
                    )
                    INSERT INTO staf (email, kode_maskapai) 
                    VALUES ((SELECT email FROM new_user), %s)
                """
                params = [email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan, kode_maskapai]
                execute_query(query_reg, params)
                
            messages.success(request, f'Registrasi berhasil untuk {email} sebagai {role.title()}. Silakan login.')
            return redirect('login')
            
        except Exception as e:
            # Mengambil dan memotong string error bawaan psycopg2 agar hanya pesan dari Trigger yang muncul
            error_msg = str(e).split('\n')[0].replace('P0001: ', '')
            messages.error(request, error_msg)
            return redirect('register')
            
    return render(request, 'register.html')

def logout_view(request):
    request.session.flush()
    return redirect('landing')

def dashboard_view(request):
    role = request.session.get('role')
    email = request.session.get('email')
    
    if not role:
        return redirect('login')

    context = {'role': role, 'name': request.session.get('name')}

    if role == 'member':
        # Query disesuaikan dengan kolom first_mid_name, last_name, mobile_number
        # Serta join ke tabel tier untuk mendapatkan nama_tier
        query_member = """
            SELECT p.salutation, p.first_mid_name, p.last_name,
                   p.kewarganegaraan, p.tanggal_lahir, p.country_code, p.mobile_number, p.email,
                   m.nomor_member, m.total_miles, m.award_miles, m.tanggal_bergabung, t.nama as nama_tier
            FROM pengguna p
            JOIN member m ON p.email = m.email
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE p.email = %s
        """
        member_data = execute_query(query_member, [email], fetch=True)
        
        if member_data:
            context['user'] = member_data[0]
            context['member'] = member_data[0]
        
        # Query disesuaikan dengan tabel redeem, transfer, dan member_award_miles_package dari SQL Dump
        query_transaksi = """
            SELECT jenis, waktu, miles 
            FROM (
                SELECT 'Redeem' as jenis, r.timestamp as waktu, -(h.miles) as miles 
                FROM redeem r 
                JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah 
                WHERE r.email_member = %s
                
                UNION ALL
                
                SELECT 'Transfer (Kirim)' as jenis, timestamp as waktu, -(jumlah) as miles 
                FROM transfer 
                WHERE email_member_1 = %s
                
                UNION ALL
                
                SELECT 'Beli Package' as jenis, p.timestamp as waktu, a.jumlah_award_miles as miles 
                FROM member_award_miles_package p 
                JOIN award_miles_package a ON p.id_award_miles_package = a.id 
                WHERE p.email_member = %s
            ) AS riwayat
            ORDER BY waktu DESC LIMIT 5
        """
        context['recent_transactions'] = execute_query(query_transaksi, [email, email, email], fetch=True)

    elif role == 'staf':
        # Menyesuaikan query staf dan JOIN ke maskapai untuk nama_maskapai
        query_staf = """
            SELECT p.salutation, p.first_mid_name, p.last_name,
                   p.kewarganegaraan, p.tanggal_lahir, p.country_code, p.mobile_number, p.email,
                   s.id_staf, mas.nama_maskapai
            FROM pengguna p
            JOIN staf s ON p.email = s.email
            JOIN maskapai mas ON s.kode_maskapai = mas.kode_maskapai
            WHERE p.email = %s
        """
        staf_data = execute_query(query_staf, [email], fetch=True)
        
        if staf_data:
            context['user'] = staf_data[0]
            context['staf'] = staf_data[0]

        # Menyesuaikan nama tabel menjadi claim_missing_miles
        query_klaim = """
            SELECT 
                COUNT(CASE WHEN status_penerimaan = 'Menunggu' THEN 1 END) as menunggu,
                COUNT(CASE WHEN status_penerimaan = 'Disetujui' THEN 1 END) as disetujui,
                COUNT(CASE WHEN status_penerimaan = 'Ditolak' THEN 1 END) as ditolak
            FROM claim_missing_miles
        """
        klaim_data = execute_query(query_klaim, fetch=True)
        if klaim_data:
            context['klaim'] = klaim_data[0]

    return render(request, 'dashboard.html', context)

def daftar_mitra(request):
    if request.session.get('role') != 'staf': return redirect('dashboard')
    
    query = """
        SELECT m.email_mitra, m.id_penyedia, m.nama_mitra, m.tanggal_kerja_sama 
        FROM MITRA m
        ORDER BY m.tanggal_kerja_sama DESC
    """
    mitra_list = execute_query(query, fetch=True)
    return render(request, 'mitra.html', {'mitra_list': mitra_list})

def tambah_mitra(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        nama = request.POST.get('nama')
        tanggal = request.POST.get('tanggal')
        
        try:
            # Asumsi: Insert ke superclass PENYEDIA dulu untuk dapat id_penyedia
            insert_query = """
                WITH new_penyedia AS (
                    INSERT INTO PENYEDIA (nama_penyedia) VALUES (%s) RETURNING id
                )
                INSERT INTO MITRA (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama) 
                VALUES (%s, (SELECT id FROM new_penyedia), %s, %s)
            """
            execute_query(insert_query, [nama, email, nama, tanggal])
            messages.success(request, 'Mitra berhasil ditambahkan.')
        except Exception as e:
            # Memunculkan pesan trigger dari Supabase jika ada (misal: duplikat)
            messages.error(request, f'{e}')
            
    return redirect('daftar_mitra')

def edit_mitra(request, email_mitra):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        tanggal = request.POST.get('tanggal')
        try:
            execute_query("""
                UPDATE MITRA 
                SET nama_mitra = %s, tanggal_kerja_sama = %s 
                WHERE email_mitra = %s
            """, [nama, tanggal, email_mitra])
            messages.success(request, 'Mitra berhasil diubah.')
        except Exception as e:
            messages.error(request, f'{e}')
            
    return redirect('daftar_mitra')

def hapus_mitra(request, email_mitra):
    if request.method == 'POST':
        try:
            execute_query("DELETE FROM MITRA WHERE email_mitra = %s", [email_mitra])
            messages.success(request, 'Mitra berhasil dihapus.')
        except Exception as e:
            messages.error(request, f'{e}')
            
    return redirect('daftar_mitra')

def daftar_hadiah(request):
    if request.session.get('role') != 'staf': return redirect('dashboard')
    
    query_hadiah = """
        SELECT h.kode_hadiah, h.nama, h.miles, h.deskripsi, h.valid_start_date, h.program_end, 
               h.id_penyedia, p.nama_penyedia 
        FROM HADIAH h
        JOIN PENYEDIA p ON h.id_penyedia = p.id
        ORDER BY h.valid_start_date DESC
    """
    hadiah_list = execute_query(query_hadiah, fetch=True)
    
    query_penyedia = "SELECT id, nama_penyedia FROM PENYEDIA"
    penyedia_list = execute_query(query_penyedia, fetch=True)
    
    return render(request, 'hadiah.html', {'hadiah_list': hadiah_list, 'penyedia_list': penyedia_list})

def tambah_hadiah(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        id_penyedia = request.POST.get('id_penyedia')
        miles = request.POST.get('miles')
        deskripsi = request.POST.get('deskripsi')
        start_date = request.POST.get('valid_start_date')
        end_date = request.POST.get('program_end')
        
        query = """
            INSERT INTO HADIAH (nama, id_penyedia, miles, deskripsi, valid_start_date, program_end)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING kode_hadiah
        """
        try:
            result = execute_query(query, [nama, id_penyedia, miles, deskripsi, start_date, end_date], fetch=True)
            kode_hadiah = result[0]['kode_hadiah'] if result else None
            if kode_hadiah:
                messages.success(request, f'Hadiah berhasil ditambahkan dengan kode {kode_hadiah}.')
            else:
                messages.success(request, 'Hadiah berhasil ditambahkan.')
        except Exception as e:
            messages.error(request, f'{e}')
            
    return redirect('daftar_hadiah')

def edit_hadiah(request, kode_hadiah):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        id_penyedia = request.POST.get('id_penyedia')
        miles = request.POST.get('miles')
        deskripsi = request.POST.get('deskripsi')
        start_date = request.POST.get('valid_start_date')
        end_date = request.POST.get('program_end')
        
        query = """
            UPDATE HADIAH 
            SET nama = %s, id_penyedia = %s, miles = %s, deskripsi = %s, valid_start_date = %s, program_end = %s
            WHERE kode_hadiah = %s
        """
        try:
            execute_query(query, [nama, id_penyedia, miles, deskripsi, start_date, end_date, kode_hadiah])
            messages.success(request, 'Hadiah berhasil diubah.')
        except Exception as e:
            messages.error(request, f'{e}')
            
    return redirect('daftar_hadiah')

def hapus_hadiah(request, kode_hadiah):
    if request.method == 'POST':
        try:
            execute_query("DELETE FROM HADIAH WHERE kode_hadiah = %s", [kode_hadiah])
            messages.success(request, 'Hadiah berhasil dihapus.')
        except Exception as e:
            messages.error(request, f'{e}')
            
    return redirect('daftar_hadiah')


def manajemen_member_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if role != 'staf':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Staf.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'tambah':
            messages.success(request, 'Member dummy baru berhasil ditambahkan!')
            
        elif action == 'edit':
            messages.success(request, 'Data member dummy berhasil diperbarui!')
            
        elif action == 'hapus':
            messages.success(request, 'Member dummy berhasil dihapus!')
            
        return redirect('manajemen_member')
        
    dummy_members = [
        {
            'nomor_member': 'M0001', 'email': 'john@example.com', 'salutation': 'Mr.',
            'nama_depan': 'John', 'nama_tengah': 'William', 'nama_belakang': 'Doe',
            'kewarganegaraan': 'Indonesia', 'country_code': '+62', 'nomor_hp': '81234567890',
            'tanggal_lahir': '1990-05-15', 'tier': 'Gold', 'total_miles': 45000, 
            'award_miles': 32000, 'tanggal_bergabung': '2024-01-15'
        },
        {
            'nomor_member': 'M0002', 'email': 'jane@example.com', 'salutation': 'Mrs.',
            'nama_depan': 'Jane', 'nama_tengah': '', 'nama_belakang': 'Smith',
            'kewarganegaraan': 'Indonesia', 'country_code': '+62', 'nomor_hp': '8987654321',
            'tanggal_lahir': '1985-10-20', 'tier': 'Silver', 'total_miles': 20000, 
            'award_miles': 15000, 'tanggal_bergabung': '2024-03-10'
        }
    ]

    search_query = request.GET.get('q', '').strip()
    filter_tier = request.GET.get('tier', '').strip()

    filtered_members = dummy_members
    if search_query:
        search_lower = search_query.lower()
        filtered_members = [
            member for member in filtered_members
            if search_lower in member['nomor_member'].lower()
            or search_lower in member['email'].lower()
            or search_lower in f"{member['salutation']} {member['nama_depan']} {member['nama_tengah']} {member['nama_belakang']}".lower()
        ]

    if filter_tier:
        filtered_members = [
            member for member in filtered_members
            if member['tier'].lower() == filter_tier.lower()
        ]

    context = {
        'role': role,
        'name': name,
        'member_list': filtered_members,
        'search_query': search_query,
        'filter_tier': filter_tier,
    }
    return render(request, 'manajemen_member.html', context)


def manajemen_identitas_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'tambah':
            messages.success(request, 'Identitas baru berhasil ditambahkan!')
        elif action == 'edit':
            messages.success(request, 'Data identitas berhasil diperbarui!')
        elif action == 'hapus':
            messages.success(request, 'Identitas berhasil dihapus!')
            
        return redirect('manajemen_identitas')
        
    dummy_identitas = [
        {
            'no_dokumen': 'A12345678', 'jenis': 'Paspor', 'negara': 'Indonesia',
            'terbit': '2020-01-15', 'habis': '2030-01-15', 'status': 'Aktif'
        },
        {
            'no_dokumen': '3275012345678901', 'jenis': 'KTP', 'negara': 'Indonesia',
            'terbit': '2019-06-01', 'habis': '2024-06-01', 'status': 'Kedaluwarsa'
        }
    ]

    context = {
        'role': role,
        'name': name,
        'identitas_list': dummy_identitas
    }
    return render(request, 'manajemen_identitas.html', context)


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
    email = request.session.get('email')
    
    if not role:
        return redirect('login')

    if request.method == 'POST':
        try:
            update_pengguna = """
                UPDATE pengguna
                SET salutation = %s,
                    first_mid_name = %s,
                    last_name = %s,
                    country_code = %s,
                    mobile_number = %s,
                    tanggal_lahir = %s,
                    kewarganegaraan = %s
                WHERE email = %s
            """
            execute_query(update_pengguna, [
                request.POST.get('salutation'),
                request.POST.get('first_name'),
                request.POST.get('last_name'),
                request.POST.get('country_code'),
                request.POST.get('phone'),
                request.POST.get('birth_date'),
                request.POST.get('nationality'),
                email
            ])

            if role == 'staf' and request.POST.get('maskapai'):
                kode_maskapai = resolve_kode_maskapai(request.POST.get('maskapai'))
                if not kode_maskapai:
                    messages.error(request, "Kode maskapai tidak ditemukan.")
                    return redirect('pengaturan_profil')
                execute_query("UPDATE staf SET kode_maskapai = %s WHERE email = %s", [kode_maskapai, email])

            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if old_password or new_password or confirm_password:
                current = execute_query("SELECT password FROM pengguna WHERE email = %s", [email], fetch=True)
                if not current or current[0]['password'] != old_password:
                    messages.error(request, "Password lama tidak sesuai.")
                    return redirect('pengaturan_profil')
                if not new_password or new_password != confirm_password:
                    messages.error(request, "Konfirmasi password baru tidak sesuai.")
                    return redirect('pengaturan_profil')
                execute_query("UPDATE pengguna SET password = %s WHERE email = %s", [new_password, email])

            messages.success(request, 'Profil berhasil diperbarui!')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui profil: {e}')
        return redirect('pengaturan_profil')

    if role == 'member':
        query = """
            SELECT p.email, p.salutation, p.first_mid_name, p.last_name,
                   p.country_code, p.mobile_number, p.tanggal_lahir, p.kewarganegaraan,
                   m.nomor_member, m.tanggal_bergabung
            FROM pengguna p
            JOIN member m ON p.email = m.email
            WHERE p.email = %s
        """
    else:
        query = """
            SELECT p.email, p.salutation, p.first_mid_name, p.last_name,
                   p.country_code, p.mobile_number, p.tanggal_lahir, p.kewarganegaraan,
                   s.id_staf, s.kode_maskapai, mas.nama_maskapai
            FROM pengguna p
            JOIN staf s ON p.email = s.email
            LEFT JOIN maskapai mas ON s.kode_maskapai = mas.kode_maskapai
            WHERE p.email = %s
        """

    profile_rows = execute_query(query, [email], fetch=True)
    if not profile_rows:
        messages.error(request, "Profil tidak ditemukan.")
        return redirect('dashboard')

    row = profile_rows[0]
    profile_data = {
        'email': row['email'],
        'salutation': row['salutation'],
        'first_name': row['first_mid_name'],
        'last_name': row['last_name'],
        'country_code': row['country_code'],
        'phone': row['mobile_number'],
        'nationality': row['kewarganegaraan'],
        'birth_date': row['tanggal_lahir'].isoformat() if row['tanggal_lahir'] else '',
    }

    if role == 'member':
        profile_data.update({
            'nomor_member': row['nomor_member'],
            'tgl_bergabung': row['tanggal_bergabung'].isoformat() if row['tanggal_bergabung'] else ''
        })
    else:
        profile_data.update({
            'id_staf': row['id_staf'],
            'maskapai': row['kode_maskapai'],
            'nama_maskapai': row.get('nama_maskapai') or row['kode_maskapai']
        })

    return render(request, 'pengaturan_profil.html', {
        'role': role, 
        'name': name, 
        'profile': profile_data
    })

def klaim_miles_view(request):
    email_user = request.session.get('email')
    query = """
        SELECT c.*, mas.nama_maskapai,
               c.flight_number AS nomor_penerbangan,
               c.kelas_kabin AS kelas,
               c.pnr AS kode_pnr
        FROM claim_missing_miles c
        LEFT JOIN maskapai mas ON c.maskapai = mas.kode_maskapai
        WHERE c.email_member = %s
        ORDER BY c.tanggal_penerbangan DESC
    """
    klaim_list = execute_query(query, [email_user], fetch=True)
    maskapai_choices = execute_query(
        "SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai",
        fetch=True
    )
    bandara_choices = execute_query(
        "SELECT iata_code, nama, kota FROM bandara ORDER BY iata_code",
        fetch=True
    )
    return render(request, 'klaim_miles.html', {
        'klaim_list': klaim_list,
        'maskapai_choices': maskapai_choices,
        'bandara_choices': bandara_choices,
        'kelas_choices': ['Economy', 'Business', 'First'],
    })

def resolve_kode_maskapai(maskapai_input):
    maskapai = (maskapai_input or '').strip()
    if not maskapai:
        return None

    query = """
        SELECT kode_maskapai
        FROM maskapai
        WHERE UPPER(kode_maskapai) = UPPER(%s)
           OR LOWER(nama_maskapai) = LOWER(%s)
        LIMIT 1
    """
    result = execute_query(query, [maskapai, maskapai], fetch=True)
    return result[0]['kode_maskapai'] if result else None

def resolve_iata_code(bandara_input):
    bandara = (bandara_input or '').strip()
    if not bandara:
        return None

    query = """
        SELECT iata_code
        FROM bandara
        WHERE UPPER(iata_code) = UPPER(%s)
           OR LOWER(nama) = LOWER(%s)
           OR LOWER(kota) = LOWER(%s)
        LIMIT 1
    """
    result = execute_query(query, [bandara, bandara, bandara], fetch=True)
    return result[0]['iata_code'] if result else None

def normalize_kelas_kabin(kelas_input):
    kelas = (kelas_input or '').strip().lower()
    if kelas == 'business':
        return 'Business'
    if kelas in ['first', 'first class']:
        return 'First'
    return 'Economy'

def ajukan_klaim(request):
    if request.method == "POST":
        email_member = request.session.get('email')
        try:
            kode_maskapai = resolve_kode_maskapai(request.POST.get('nama_maskapai'))
            if not kode_maskapai:
                messages.error(request, "Maskapai tidak ditemukan. Gunakan kode seperti GA/SQ/MH atau nama maskapai yang valid.")
                return redirect('klaim_miles')
            bandara_asal = resolve_iata_code(request.POST.get('bandara_asal'))
            bandara_tujuan = resolve_iata_code(request.POST.get('bandara_tujuan'))
            if not bandara_asal or not bandara_tujuan:
                messages.error(request, "Bandara tidak ditemukan. Gunakan kode seperti CGK/DPS/SIN atau nama bandara yang valid.")
                return redirect('klaim_miles')

            query = """
                INSERT INTO claim_missing_miles 
                (email_member, maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan,
                 flight_number, nomor_tiket, kelas_kabin, pnr, status_penerimaan, timestamp)
                VALUES (%s, %s, UPPER(%s), UPPER(%s), %s, %s, %s, %s, %s, 'Menunggu', NOW())
            """
            execute_query(query, [
                email_member,
                kode_maskapai,
                bandara_asal,
                bandara_tujuan,
                request.POST.get('tanggal_penerbangan'),
                request.POST.get('nomor_penerbangan'),
                request.POST.get('nomor_tiket'),
                normalize_kelas_kabin(request.POST.get('kelas')),
                (request.POST.get('kode_pnr') or '').strip().upper()
            ])
            messages.success(request, "Klaim berhasil diajukan!")
        except Exception as e:
            messages.error(request, f"Gagal mengajukan klaim: {e}")
            
    return redirect('klaim_miles')

def edit_klaim(request, id):
    if request.method == "POST":
        email_user = request.session.get('email')
        try:
            check_query = "SELECT status_penerimaan FROM claim_missing_miles WHERE id = %s AND email_member = %s"
            curr = execute_query(check_query, [id, email_user], fetch=True)
            
            if not curr:
                messages.error(request, "Data tidak ditemukan.")
            elif curr[0]['status_penerimaan'] != 'Menunggu':
                messages.error(request, "Klaim tidak dapat diubah karena sudah diproses.")
            else:
                kode_maskapai = resolve_kode_maskapai(request.POST.get('nama_maskapai'))
                if not kode_maskapai:
                    messages.error(request, "Maskapai tidak ditemukan. Gunakan kode seperti GA/SQ/MH atau nama maskapai yang valid.")
                    return redirect('klaim_miles')
                bandara_asal = resolve_iata_code(request.POST.get('bandara_asal'))
                bandara_tujuan = resolve_iata_code(request.POST.get('bandara_tujuan'))
                if not bandara_asal or not bandara_tujuan:
                    messages.error(request, "Bandara tidak ditemukan. Gunakan kode seperti CGK/DPS/SIN atau nama bandara yang valid.")
                    return redirect('klaim_miles')

                update_query = """
                    UPDATE claim_missing_miles 
                    SET maskapai = %s,
                        bandara_asal = UPPER(%s),
                        bandara_tujuan = UPPER(%s), 
                        tanggal_penerbangan = %s,
                        flight_number = %s,
                        nomor_tiket = %s,
                        kelas_kabin = %s,
                        pnr = %s
                    WHERE id = %s AND email_member = %s
                """
                execute_query(update_query, [
                    kode_maskapai,
                    bandara_asal, 
                    bandara_tujuan,
                    request.POST.get('tanggal_penerbangan'), 
                    request.POST.get('nomor_penerbangan'),
                    request.POST.get('nomor_tiket'),
                    normalize_kelas_kabin(request.POST.get('kelas')),
                    (request.POST.get('kode_pnr') or '').strip().upper(),
                    id,
                    email_user
                ])
                messages.success(request, f"Klaim #{id} berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal: {e}")
            
    return redirect('klaim_miles')

def batalkan_klaim(request, id):
    email_user = request.session.get('email')
    try:
        query = """
            DELETE FROM claim_missing_miles
            WHERE id = %s AND email_member = %s AND status_penerimaan = 'Menunggu'
            RETURNING id
        """
        deleted = execute_query(query, [id, email_user], fetch=True)
        if deleted:
            messages.success(request, "Pengajuan klaim berhasil dibatalkan.")
        else:
            messages.error(request, "Klaim tidak ditemukan atau sudah diproses.")
    except Exception:
        messages.error(request, "Gagal membatalkan klaim.")
    return redirect('klaim_miles')

def kelola_klaim_staf(request):
    query = """
        SELECT c.*, p.first_mid_name, p.last_name, mas.nama_maskapai,
               c.flight_number AS nomor_penerbangan,
               c.kelas_kabin AS kelas,
               c.pnr AS kode_pnr
        FROM claim_missing_miles c
        JOIN pengguna p ON c.email_member = p.email
        LEFT JOIN maskapai mas ON c.maskapai = mas.kode_maskapai
        ORDER BY CASE WHEN status_penerimaan = 'Menunggu' THEN 1 ELSE 2 END, tanggal_penerbangan DESC
    """
    klaim_staf_list = execute_query(query, fetch=True)
    maskapai_choices = execute_query(
        "SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai",
        fetch=True
    )
    return render(request, 'kelola_klaim_staf.html', {
        'klaim_staf_list': klaim_staf_list,
        'maskapai_choices': maskapai_choices,
    })

def setujui_klaim(request, pk):
    email_staf = request.session.get('email')
    try:
        query_update = """
            UPDATE claim_missing_miles
            SET status_penerimaan = 'Disetujui', email_staf = %s
            WHERE id = %s AND status_penerimaan = 'Menunggu'
            RETURNING email_member
        """
        updated = execute_query(query_update, [email_staf, pk], fetch=True)
        if not updated:
            messages.error(request, "Klaim tidak ditemukan atau sudah diproses.")
            return redirect('kelola_klaim_staf')
        email_member = updated[0]['email_member']
        messages.success(request, f"Klaim #{pk} disetujui.")
    except Exception:
        messages.error(request, "Gagal memproses persetujuan.")
    return redirect('kelola_klaim_staf')

def tolak_klaim(request, pk):
    if request.method == "POST":
        email_staf = request.session.get('email')
        try:
            query = """
                UPDATE claim_missing_miles
                SET status_penerimaan = 'Ditolak', email_staf = %s
                WHERE id = %s AND status_penerimaan = 'Menunggu'
                RETURNING id
            """
            updated = execute_query(query, [email_staf, pk], fetch=True)
            if updated:
                messages.success(request, f"Klaim #{pk} telah ditolak.")
            else:
                messages.error(request, "Klaim tidak ditemukan atau sudah diproses.")
        except Exception:
            messages.error(request, "Gagal memproses penolakan.")
    return redirect('kelola_klaim_staf')

def transfer_miles(request):
    email_user = request.session.get('email')
    res_miles = execute_query("SELECT award_miles FROM member WHERE email = %s", [email_user], fetch=True)
    award_miles_tersedia = res_miles[0]['award_miles'] if res_miles else 0
    
    query_history = """
        SELECT t.*,
               CASE WHEN t.email_member_1 = %s THEN 'Kirim' ELSE 'Terima' END AS tipe,
               CASE WHEN t.email_member_1 = %s THEN -t.jumlah ELSE t.jumlah END AS jumlah_miles,
               CASE WHEN t.email_member_1 = %s THEN t.email_member_2 ELSE t.email_member_1 END AS email_member,
               CASE WHEN t.email_member_1 = %s
                    THEN CONCAT(p2.first_mid_name, ' ', p2.last_name)
                    ELSE CONCAT(p1.first_mid_name, ' ', p1.last_name)
               END AS nama_member
        FROM transfer t
        JOIN pengguna p1 ON t.email_member_1 = p1.email
        JOIN pengguna p2 ON t.email_member_2 = p2.email
        WHERE email_member_1 = %s OR email_member_2 = %s 
        ORDER BY timestamp DESC
    """
    riwayat_transfer = execute_query(query_history, [email_user, email_user, email_user, email_user, email_user, email_user], fetch=True)
    return render(request, 'transfer_miles.html', {
        'award_miles_tersedia': award_miles_tersedia,
        'riwayat_transfer': riwayat_transfer
    })

def proses_transfer(request):
    if request.method == "POST":
        email_pengirim = request.session.get('email')
        email_penerima = (request.POST.get('email_penerima') or '').strip().lower()
        try:
            jumlah_miles = int(request.POST.get('jumlah_miles', 0))
        except (TypeError, ValueError):
            jumlah_miles = 0
        catatan = request.POST.get('catatan', '')

        try:
            if jumlah_miles <= 0:
                messages.error(request, "Jumlah miles harus lebih dari 0.")
                return redirect('transfer_miles')

            res_penerima = execute_query("SELECT email FROM member WHERE LOWER(email) = LOWER(%s)", [email_penerima], fetch=True)
            if not res_penerima:
                messages.error(request, "Email member penerima tidak ditemukan.")
                return redirect('transfer_miles')
            
            email_penerima = res_penerima[0]['email']
            if email_penerima == email_pengirim:
                messages.error(request, "Tidak dapat transfer ke diri sendiri.")
                return redirect('transfer_miles')

            res_saldo = execute_query("SELECT award_miles FROM member WHERE email = %s", [email_pengirim], fetch=True)
            if not res_saldo or res_saldo[0]['award_miles'] < jumlah_miles:
                messages.error(request, "Saldo Award Miles tidak mencukupi.")
                return redirect('transfer_miles')
            
            execute_query("UPDATE member SET award_miles = award_miles - %s WHERE email = %s", [jumlah_miles, email_pengirim])
            execute_query("UPDATE member SET award_miles = award_miles + %s WHERE email = %s", [jumlah_miles, email_penerima])
            
            query_insert = """
                INSERT INTO transfer (email_member_1, email_member_2, timestamp, jumlah, catatan) 
                VALUES (%s, %s, NOW(), %s, %s)
            """
            execute_query(query_insert, [email_pengirim, email_penerima, jumlah_miles, catatan])
            
            messages.success(request, f"Berhasil transfer {jumlah_miles} miles.")
        except Exception as e:
            messages.error(request, f"Gagal: {e}")
            
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
    filter_dari = request.GET.get('dari', '')
    filter_sampai = request.GET.get('sampai', '')

    filtered = DUMMY_TRANSAKSI[:]
    if filter_jenis:
        filtered = [t for t in filtered if t['jenis'] == filter_jenis]
    if filter_email:
        filtered = [t for t in filtered if filter_email.lower() in t['email_member'].lower()]
    if filter_dari:
        try:
            tanggal_dari = datetime.date.fromisoformat(filter_dari)
            filtered = [t for t in filtered if t['timestamp'].date() >= tanggal_dari]
        except ValueError:
            pass
    if filter_sampai:
        try:
            tanggal_sampai = datetime.date.fromisoformat(filter_sampai)
            filtered = [t for t in filtered if t['timestamp'].date() <= tanggal_sampai]
        except ValueError:
            pass

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
        'filter_dari': filter_dari,
        'filter_sampai': filter_sampai,
    })


def hapus_transaksi_view(request, jenis, id1, id2, id3):
    if request.session.get('role') != 'staf':
        return redirect('dashboard')

    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
    else:
        messages.success(request, 'Transaksi berhasil dihapus. Penghapusan ini bersifat permanen.')
    return redirect('laporan_transaksi')
