from django.shortcuts import render, redirect
from django.contrib import messages
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

COUNTRY_NAME_TO_CODE = {
    'Indonesia': 'IDN',
    'Malaysia': 'MYS',
    'Singapore': 'SGP',
}

COUNTRY_CODE_TO_NAME = {code: name for name, code in COUNTRY_NAME_TO_CODE.items()}

def get_db_connection():
    return psycopg2.connect(
        host="aws-1-ap-northeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.bragfwhkwwwulxfdsiqm",
        password="Nainggolan123",
        port="6543",
        options="-c search_path=aeromiles"
    )

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


def format_db_error(error):
    return str(error).split('\n')[0].replace('P0001: ', '').strip()


def split_first_middle_name(full_name):
    parts = (full_name or '').split()
    if not parts:
        return '', ''
    return parts[0], ' '.join(parts[1:])


def combine_first_middle_name(first_name, middle_name):
    return ' '.join(part for part in [first_name.strip(), middle_name.strip()] if part).strip()


def country_name_from_code(country_code):
    return COUNTRY_CODE_TO_NAME.get(country_code, country_code)


def country_code_from_name(country_name):
    return COUNTRY_NAME_TO_CODE.get(country_name, country_name)

def landing_view(request):
    if request.session.get('role'):
        return redirect('dashboard')
    return render(request, 'landing.html')

def login_view(request):
    if request.session.get('role'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            query_user = "SELECT * FROM verify_login(%s, %s)"
            user_data = execute_query(query_user, [email, password], fetch=True)
            
            if user_data:
                user = user_data[0]
                
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
                        
                request.session['role'] = role
                request.session['email'] = user['email']
                request.session['name'] = f"{user['salutation']} {user['first_mid_name']} {user['last_name']}".strip()
                
                return redirect('dashboard')
                
        except Exception as e:
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

    tier_choices = execute_query(
        "SELECT id_tier, nama FROM tier ORDER BY id_tier",
        fetch=True
    )
    tier_name_to_id = {tier['nama']: tier['id_tier'] for tier in tier_choices}

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            if action == 'tambah':
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password', '').strip()
                salutation = request.POST.get('salutation', '').strip()
                nama_depan = request.POST.get('nama_depan', '').strip()
                nama_tengah = request.POST.get('nama_tengah', '').strip()
                nama_belakang = request.POST.get('nama_belakang', '').strip()
                kewarganegaraan = country_code_from_name(request.POST.get('kewarganegaraan', '').strip())
                country_code = request.POST.get('country_code', '').strip()
                nomor_hp = request.POST.get('nomor_hp', '').strip()
                tanggal_lahir = request.POST.get('tanggal_lahir')
                first_mid_name = combine_first_middle_name(nama_depan, nama_tengah)

                query_tambah_member = """
                    WITH new_user AS (
                        INSERT INTO pengguna (
                            email, password, salutation, first_mid_name, last_name,
                            country_code, mobile_number, tanggal_lahir, kewarganegaraan
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING email
                    )
                    INSERT INTO member (email, tanggal_bergabung, id_tier, award_miles, total_miles)
                    VALUES ((SELECT email FROM new_user), CURRENT_DATE, 'T01', 0, 0)
                    RETURNING nomor_member
                """
                result = execute_query(
                    query_tambah_member,
                    [
                        email, password, salutation, first_mid_name, nama_belakang,
                        country_code, nomor_hp, tanggal_lahir, kewarganegaraan
                    ],
                    fetch=True
                )
                nomor_member = result[0]['nomor_member'] if result else '-'
                messages.success(request, f'Member {nomor_member} berhasil ditambahkan.')

            elif action == 'edit':
                nomor_member = request.POST.get('nomor_member', '').strip()
                salutation = request.POST.get('salutation', '').strip()
                nama_depan = request.POST.get('nama_depan', '').strip()
                nama_tengah = request.POST.get('nama_tengah', '').strip()
                nama_belakang = request.POST.get('nama_belakang', '').strip()
                kewarganegaraan = country_code_from_name(request.POST.get('kewarganegaraan', '').strip())
                country_code = request.POST.get('country_code', '').strip()
                nomor_hp = request.POST.get('nomor_hp', '').strip()
                tanggal_lahir = request.POST.get('tanggal_lahir')
                tier_name = request.POST.get('tier', '').strip()
                id_tier = tier_name_to_id.get(tier_name)
                first_mid_name = combine_first_middle_name(nama_depan, nama_tengah)

                if not id_tier:
                    raise ValueError('Tier yang dipilih tidak valid.')

                query_edit_member = """
                    WITH target_member AS (
                        SELECT email
                        FROM member
                        WHERE nomor_member = %s
                    ),
                    updated_pengguna AS (
                        UPDATE pengguna
                        SET salutation = %s,
                            first_mid_name = %s,
                            last_name = %s,
                            country_code = %s,
                            mobile_number = %s,
                            tanggal_lahir = %s,
                            kewarganegaraan = %s
                        WHERE email = (SELECT email FROM target_member)
                        RETURNING email
                    ),
                    updated_member AS (
                        UPDATE member
                        SET id_tier = %s
                        WHERE nomor_member = %s
                        RETURNING nomor_member
                    )
                    SELECT nomor_member FROM updated_member
                """
                result = execute_query(
                    query_edit_member,
                    [
                        nomor_member, salutation, first_mid_name, nama_belakang,
                        country_code, nomor_hp, tanggal_lahir, kewarganegaraan,
                        id_tier, nomor_member
                    ],
                    fetch=True
                )

                if not result:
                    raise ValueError('Data member tidak ditemukan.')

                messages.success(request, f'Data member {nomor_member} berhasil diperbarui.')

            elif action == 'hapus':
                nomor_member = request.POST.get('nomor_member', '').strip()
                query_hapus_member = """
                    WITH deleted_member AS (
                        DELETE FROM member
                        WHERE nomor_member = %s
                        RETURNING email
                    )
                    DELETE FROM pengguna
                    WHERE email IN (SELECT email FROM deleted_member)
                    RETURNING email
                """
                result = execute_query(query_hapus_member, [nomor_member], fetch=True)

                if not result:
                    raise ValueError('Data member tidak ditemukan.')

                messages.success(request, f'Member {nomor_member} berhasil dihapus.')

        except Exception as error:
            messages.error(request, format_db_error(error))

        return redirect('manajemen_member')

    search_query = request.GET.get('q', '').strip()
    filter_tier = request.GET.get('tier', '').strip()

    member_query = """
        SELECT
            m.nomor_member,
            m.email,
            p.salutation,
            p.first_mid_name,
            p.last_name,
            p.kewarganegaraan,
            p.country_code,
            p.mobile_number,
            p.tanggal_lahir,
            t.nama AS tier,
            m.total_miles,
            m.award_miles,
            m.tanggal_bergabung
        FROM member m
        JOIN pengguna p ON p.email = m.email
        JOIN tier t ON t.id_tier = m.id_tier
        WHERE (%s = '' OR
            m.nomor_member ILIKE %s OR
            m.email ILIKE %s OR
            CONCAT_WS(' ', p.salutation, p.first_mid_name, p.last_name) ILIKE %s
        )
        AND (%s = '' OR t.nama = %s)
        ORDER BY m.nomor_member ASC
    """
    like_search = f"%{search_query}%"
    filtered_members = execute_query(
        member_query,
        [search_query, like_search, like_search, like_search, filter_tier, filter_tier],
        fetch=True
    )

    for member in filtered_members:
        nama_depan, nama_tengah = split_first_middle_name(member.get('first_mid_name'))
        member['nama_depan'] = nama_depan
        member['nama_tengah'] = nama_tengah
        member['nama_belakang'] = member.get('last_name', '')
        member['nomor_hp'] = member.get('mobile_number', '')
        member['kewarganegaraan'] = country_name_from_code(member.get('kewarganegaraan'))

    context = {
        'role': role,
        'name': name,
        'member_list': filtered_members,
        'tier_choices': tier_choices,
        'search_query': search_query,
        'filter_tier': filter_tier,
    }
    return render(request, 'manajemen_member.html', context)


def manajemen_identitas_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    email = request.session.get('email')
    
    if role != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            if action == 'tambah':
                no_dokumen = request.POST.get('no_dokumen', '').strip()
                jenis = request.POST.get('jenis', '').strip()
                negara = country_code_from_name(request.POST.get('negara', '').strip())
                terbit = request.POST.get('terbit')
                habis = request.POST.get('habis')

                execute_query(
                    """
                    INSERT INTO identitas (nomor, email_member, tanggal_habis, tanggal_terbit, negara_penerbit, jenis)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [no_dokumen, email, habis, terbit, negara, jenis]
                )
                messages.success(request, 'Identitas baru berhasil ditambahkan.')

            elif action == 'edit':
                no_dokumen = request.POST.get('old_no_dokumen', '').strip()
                jenis = request.POST.get('jenis', '').strip()
                negara = country_code_from_name(request.POST.get('negara', '').strip())
                terbit = request.POST.get('terbit')
                habis = request.POST.get('habis')

                result = execute_query(
                    """
                    UPDATE identitas
                    SET jenis = %s,
                        negara_penerbit = %s,
                        tanggal_terbit = %s,
                        tanggal_habis = %s
                    WHERE nomor = %s AND email_member = %s
                    RETURNING nomor
                    """,
                    [jenis, negara, terbit, habis, no_dokumen, email],
                    fetch=True
                )

                if not result:
                    raise ValueError('Data identitas tidak ditemukan.')

                messages.success(request, 'Data identitas berhasil diperbarui.')

            elif action == 'hapus':
                no_dokumen = request.POST.get('no_dokumen', '').strip()
                result = execute_query(
                    """
                    DELETE FROM identitas
                    WHERE nomor = %s AND email_member = %s
                    RETURNING nomor
                    """,
                    [no_dokumen, email],
                    fetch=True
                )

                if not result:
                    raise ValueError('Data identitas tidak ditemukan.')

                messages.success(request, 'Identitas berhasil dihapus.')

        except Exception as error:
            messages.error(request, format_db_error(error))

        return redirect('manajemen_identitas')

    identitas_query = """
        SELECT
            nomor AS no_dokumen,
            jenis,
            negara_penerbit,
            tanggal_terbit AS terbit,
            tanggal_habis AS habis,
            CASE
                WHEN tanggal_habis >= CURRENT_DATE THEN 'Aktif'
                ELSE 'Kedaluwarsa'
            END AS status
        FROM identitas
        WHERE email_member = %s
        ORDER BY tanggal_habis DESC, nomor ASC
    """
    identitas_list = execute_query(identitas_query, [email], fetch=True)

    for identitas in identitas_list:
        identitas['negara'] = country_name_from_code(identitas.get('negara_penerbit'))

    context = {
        'role': role,
        'name': name,
        'identitas_list': identitas_list
    }
    return render(request, 'manajemen_identitas.html', context)


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
