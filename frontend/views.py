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
        kode = request.POST.get('kode_hadiah')
        nama = request.POST.get('nama')
        id_penyedia = request.POST.get('id_penyedia')
        miles = request.POST.get('miles')
        deskripsi = request.POST.get('deskripsi')
        start_date = request.POST.get('valid_start_date')
        end_date = request.POST.get('program_end')
        
        query = """
            INSERT INTO HADIAH (kode_hadiah, nama, id_penyedia, miles, deskripsi, valid_start_date, program_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            execute_query(query, [kode, nama, id_penyedia, miles, deskripsi, start_date, end_date])
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

    context = {
        'role': role,
        'name': name,
        'member_list': dummy_members
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
