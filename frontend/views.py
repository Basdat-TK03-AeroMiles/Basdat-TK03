from django.shortcuts import render, redirect
from django.contrib import messages

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
    
    if not role:
        return redirect('login')
        
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