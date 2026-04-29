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

def logout_view(request):
    request.session.flush()
    return redirect('login')

def dashboard_view(request):
    role = request.session.get('role')
    name = request.session.get('name')
    
    if not role:
        return redirect('login')
        
    return render(request, 'dashboard.html', {'role': role, 'name': name})