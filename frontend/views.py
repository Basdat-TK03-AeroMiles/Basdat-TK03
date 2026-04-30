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
            return redirect('dashboard')
        elif email == 'member@aeromiles.com' and password == 'member123':
            request.session['role'] = 'member'
            request.session['name'] = 'Mr. John William Doe'
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