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

def execute_query(query, params=None, fetch=False, return_notices=False):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(query, params)
        notices = [n.strip() for n in conn.notices] if conn.notices else []
        if fetch:
            result = cursor.fetchall()
            conn.commit()
            if return_notices:
                return result, notices
            return result
        else:
            conn.commit()
            if return_notices:
                return None, notices
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
            messages.error(request, format_db_error(e))
            
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
        updated, notices = execute_query(query_update, [email_staf, pk], fetch=True, return_notices=True)
        if not updated:
            messages.error(request, "Klaim tidak ditemukan atau sudah diproses.")
            return redirect('kelola_klaim_staf')

        success_notices = [
            notice.replace('NOTICE:  ', '').replace('NOTICE:', '').strip()
            for notice in notices
            if 'SUKSES:' in notice
        ]
        if success_notices:
            for notice in success_notices:
                messages.success(request, notice)
    except Exception as e:
        messages.error(request, format_db_error(e))
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

            result, notices = execute_query(
                "SELECT sp_transfer_miles(%s, %s, %s, %s) AS message",
                [email_pengirim, email_penerima, jumlah_miles, catatan],
                fetch=True,
                return_notices=True
            )

            if result:
                messages.success(request, result[0]['message'])
            for notice in notices:
                if 'SUKSES:' in notice:
                    messages.success(request, notice.replace('NOTICE:  ', '').replace('NOTICE:', '').strip())
        except Exception as e:
            messages.error(request, format_db_error(e))
            
    return redirect('transfer_miles')

AWARD_MILES = 0


def redeem_hadiah_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    email_member = request.session.get('email')

    if request.method == 'POST':
        kode_hadiah = request.POST.get('kode_hadiah')
        try:
            _, notices = execute_query(
                "INSERT INTO redeem (email_member, kode_hadiah, timestamp) VALUES (%s, %s, NOW())", 
                [email_member, kode_hadiah], 
                return_notices=True
            )
            # The success message is returned as a NOTICE from the Trigger.
            for notice in notices:
                if 'SUKSES:' in notice:
                    messages.success(request, notice.replace('NOTICE:  ', '').replace('NOTICE:', '').strip())
        except Exception as e:
            # The Trigger will throw an exception if validation fails (e.g. not enough miles, inactive)
            messages.error(request, format_db_error(e))
        return redirect('redeem_hadiah')

    katalog_query = """
        SELECT h.kode_hadiah, h.nama, h.miles, h.deskripsi, h.valid_start_date, h.program_end, p.nama_penyedia
        FROM hadiah h
        JOIN penyedia p ON h.id_penyedia = p.id
        WHERE h.program_end >= CURRENT_DATE
        ORDER BY h.valid_start_date DESC
    """
    hadiah_list = execute_query(katalog_query, fetch=True)

    member_res = execute_query("SELECT award_miles FROM member WHERE email = %s", [email_member], fetch=True)
    award_miles = member_res[0]['award_miles'] if member_res else 0

    riwayat_query = """
        SELECT r.timestamp, h.nama as nama_hadiah, h.miles, h.kode_hadiah
        FROM redeem r
        JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
        WHERE r.email_member = %s
        ORDER BY r.timestamp DESC
    """
    riwayat_redeem = execute_query(riwayat_query, [email_member], fetch=True)

    return render(request, 'redeem_hadiah.html', {
        'hadiah_list': hadiah_list,
        'award_miles': award_miles,
        'riwayat_redeem': riwayat_redeem,
    })


def beli_paket_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    email_member = request.session.get('email')

    if request.method == 'POST':
        id_paket = request.POST.get('id_paket')
        try:
            _, notices = execute_query(
                "INSERT INTO member_award_miles_package (email_member, id_award_miles_package, timestamp) VALUES (%s, %s, NOW())", 
                [email_member, id_paket], 
                return_notices=True
            )
            for notice in notices:
                if 'SUKSES:' in notice:
                    messages.success(request, notice.replace('NOTICE:  ', '').replace('NOTICE:', '').strip())
        except Exception as e:
            messages.error(request, format_db_error(e))
        return redirect('beli_paket')

    paket_list = execute_query("SELECT id, jumlah_award_miles, harga_paket FROM award_miles_package ORDER BY harga_paket ASC", fetch=True)
    member_res = execute_query("SELECT award_miles FROM member WHERE email = %s", [email_member], fetch=True)
    award_miles = member_res[0]['award_miles'] if member_res else 0

    return render(request, 'beli_paket.html', {
        'paket_list': paket_list,
        'award_miles': award_miles,
    })


def info_tier_view(request):
    if request.session.get('role') != 'member':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Member.')
        return redirect('dashboard')

    email_member = request.session.get('email')

    tier_list = execute_query("SELECT id_tier, nama, minimal_frekuensi_terbang, minimal_tier_miles FROM tier ORDER BY minimal_tier_miles ASC", fetch=True)
    
    query_member = """
        SELECT m.id_tier, t.nama as nama_tier, m.total_miles 
        FROM member m
        JOIN tier t ON m.id_tier = t.id_tier
        WHERE m.email = %s
    """
    member_data = execute_query(query_member, [email_member], fetch=True)
    
    if member_data:
        current_tier_id = member_data[0]['id_tier']
        nama_tier = member_data[0]['nama_tier']
        total_miles = member_data[0]['total_miles']
    else:
        current_tier_id = None
        nama_tier = '-'
        total_miles = 0

    next_tier = None
    found = False
    for t in tier_list:
        if found:
            next_tier = t
            break
        if t['id_tier'] == current_tier_id:
            found = True

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
    if request.session.get('role') != 'staf':
        messages.error(request, 'Akses Ditolak: Halaman ini khusus untuk Staf.')
        return redirect('dashboard')

    filter_jenis = request.GET.get('jenis', '')
    filter_email = request.GET.get('email', '')
    filter_dari = request.GET.get('dari', '')
    filter_sampai = request.GET.get('sampai', '')

    base_query = """
        SELECT 'redeem' AS jenis, r.email_member, h.miles AS jumlah_miles, r.timestamp,
               r.email_member AS id1, r.kode_hadiah AS id2, r.timestamp::text AS id3,
               CONCAT('Redeem: ', h.nama) AS deskripsi
        FROM redeem r
        JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
        UNION ALL
        SELECT 'package' AS jenis, mp.email_member, amp.jumlah_award_miles AS jumlah_miles, mp.timestamp,
               mp.id_award_miles_package AS id1, mp.email_member AS id2, mp.timestamp::text AS id3,
               CONCAT('Beli Paket: ', mp.id_award_miles_package, ' (', amp.jumlah_award_miles, ' miles)') AS deskripsi
        FROM member_award_miles_package mp
        JOIN award_miles_package amp ON mp.id_award_miles_package = amp.id
        UNION ALL
        SELECT 'transfer' AS jenis, t.email_member_1 AS email_member, t.jumlah AS jumlah_miles, t.timestamp,
               t.email_member_1 AS id1, t.email_member_2 AS id2, t.timestamp::text AS id3,
               CONCAT('Transfer ', t.jumlah, ' miles dari ', t.email_member_1, ' ke ', t.email_member_2) AS deskripsi
        FROM transfer t
        UNION ALL
        SELECT 'klaim' AS jenis, c.email_member, 0 AS jumlah_miles, c.timestamp,
               c.id::text AS id1, c.email_member AS id2, c.timestamp::text AS id3,
               CONCAT('Klaim Disetujui: ', c.flight_number, ' (', c.bandara_asal, ' → ', c.bandara_tujuan, ')') AS deskripsi
        FROM claim_missing_miles c
        WHERE c.status_penerimaan = 'Disetujui'
    """
    
    query = f"SELECT * FROM ({base_query}) AS all_tx WHERE 1=1"
    params = []

    if filter_jenis:
        query += " AND jenis = %s"
        params.append(filter_jenis)
    if filter_email:
        query += " AND email_member ILIKE %s"
        params.append(f"%{filter_email}%")
    if filter_dari:
        query += " AND timestamp >= %s"
        params.append(filter_dari)
    if filter_sampai:
        query += " AND timestamp <= %s"
        params.append(filter_sampai + ' 23:59:59')

    query += " ORDER BY timestamp DESC"
    transaksi_list = execute_query(query, params, fetch=True)

    stats = {
        'total_miles_beredar': (execute_query("SELECT COALESCE(SUM(total_miles), 0) AS v FROM member", fetch=True)[0]['v']),
        'redeem_bulan_ini': (execute_query("SELECT COUNT(*) AS v FROM redeem WHERE DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)", fetch=True)[0]['v']),
        'klaim_disetujui': (execute_query("SELECT COUNT(*) AS v FROM claim_missing_miles WHERE status_penerimaan = 'Disetujui'", fetch=True)[0]['v']),
    }

    try:
        top_miles, notices = execute_query("SELECT * FROM get_top_5_member()", fetch=True, return_notices=True)
        for notice in notices:
            if 'SUKSES:' in notice:
                messages.success(request, notice.replace('NOTICE:  ', '').replace('NOTICE:', '').strip())
    except Exception as e:
        print(f"Stored procedure get_top_5_member() gagal: {e}")
        top_miles = execute_query("""
            SELECT CONCAT(p.first_mid_name, ' ', p.last_name) AS nama, m.email, m.total_miles
            FROM member m JOIN pengguna p ON m.email = p.email
            ORDER BY m.total_miles DESC LIMIT 5
        """, fetch=True)

    top_redeem = execute_query("""
        SELECT CONCAT(p.first_mid_name, ' ', p.last_name) AS nama, r.email_member AS email, COUNT(*) AS jumlah
        FROM redeem r JOIN pengguna p ON r.email_member = p.email
        GROUP BY p.first_mid_name, p.last_name, r.email_member ORDER BY jumlah DESC LIMIT 5
    """, fetch=True)

    top_transfer = execute_query("""
        SELECT CONCAT(p.first_mid_name, ' ', p.last_name) AS nama, t.email_member_1 AS email, COUNT(*) AS jumlah
        FROM transfer t JOIN pengguna p ON t.email_member_1 = p.email
        GROUP BY p.first_mid_name, p.last_name, t.email_member_1 ORDER BY jumlah DESC LIMIT 5
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
    if request.session.get('role') != 'staf':
        return redirect('dashboard')

    if jenis == 'klaim':
        messages.error(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
        return redirect('laporan_transaksi')

    delete_queries = {
        'redeem': "DELETE FROM redeem WHERE email_member = %s AND kode_hadiah = %s AND timestamp = %s",
        'package': "DELETE FROM member_award_miles_package WHERE id_award_miles_package = %s AND email_member = %s AND timestamp = %s",
        'transfer': "DELETE FROM transfer WHERE email_member_1 = %s AND email_member_2 = %s AND timestamp = %s",
    }
    
    delete_sql = delete_queries.get(jenis)
    if not delete_sql:
        messages.error(request, 'Jenis transaksi tidak valid.')
        return redirect('laporan_transaksi')

    try:
        execute_query(delete_sql, [id1, id2, id3])
        messages.success(request, 'Transaksi berhasil dihapus. Penghapusan ini bersifat permanen.')
    except Exception as e:
        messages.error(request, f'Gagal menghapus transaksi: {e}')

    return redirect('laporan_transaksi')
