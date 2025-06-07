from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib import messages
from .models import HealthReport, NurseStatus, NurseAnnouncement
from .forms import HealthReportForm
import requests 
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import TemplateDoesNotExist
from django.http import HttpResponse

def home(request):
    return render(request, 'main/livora.html')

def nurse_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "You don't have admin privileges.")
                return redirect('nurse_login')
    else:
        form = AuthenticationForm()
    return render(request, 'main/nurse_login.html', {'form': form})

def login_box(request):
   form = AuthenticationForm()
   return render(request, 'main/partials/login.html', {'form': form})


def register_box(request):
   form = UserCreationForm()
   return render(request, 'main/partials/register.html', {'form': form})


def register(request):
   if request.method == 'POST':
       form = UserCreationForm(request.POST)
       if form.is_valid():
           form.save()
           return redirect('login')
   else:
       form = UserCreationForm()
   return render(request, 'main/register.html', {'form': form})

#login_view with API 
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        payload = {
            'key': settings.API_KEY,
            'username': username,
            'password': password,
        }

        response = requests.post('https://api.ksain.net/v1/login.php', data=payload)
        if response.status_code == 200:
            res = response.json()
            if res.get('status') == 'success':
                student_data = res.get('data', {})
                name = student_data.get('name', '')
                first_name = name.split()[0] if name else ''
                last_name = ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''

                user, created = User.objects.get_or_create(username=username)
                user.first_name = first_name
                user.last_name = last_name
                user.save()

                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('reguser_dashboard')
            else:
                messages.error(request, res.get('message', 'Login failed.'))
        else:
            messages.error(request, "Failed to contact login API.")

    return render(request, 'main/livora.html')


def C_Logout_View(request):
   logout(request)
   return redirect('livora')


def is_admin(user):
   return user.is_authenticated and user.is_staff


def is_regular_user(user):
   return user.is_authenticated and not user.is_staff

def request_history(request):
    print("Current user:", request.user.username)
    reports = HealthReport.objects.filter(user=request.user).order_by('-created_at')
    print(f"Reports count for {request.user}: {reports.count()}")
    return render(request, 'main/ruser_comp/rqst_his_std.html', {'health_reports': reports})


def reguser_dashboard(request):
   return render(request, 'dashboard.html')


@login_required(login_url='login')
@user_passes_test(is_regular_user, login_url='livora')
def reguser_dashboard(request):
   if request.method == 'POST':
       form = HealthReportForm(request.POST, request.FILES)
       if form.is_valid():
           report = form.save(commit=False)
           report.save()
           return redirect('reguser_dashboard')
   else:
       form = HealthReportForm()
   return render(request, 'main/reguser_dashboard.html', {'form': form})


@login_required(login_url='login')
@user_passes_test(is_regular_user, login_url='livora')
def submit_health_report(request):
    if request.method == 'POST':
        user = request.user
        data = request.POST.copy()
        symptoms_raw = data.get('symptoms', '')
        symptoms_list = [s.strip().lower() for s in symptoms_raw.split(',') if s.strip()]
        data.setlist('symptoms', symptoms_list)

        form = HealthReportForm(data)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = user
            report.save()
            return redirect('reguser_dashboard')
        else:
            print("Form invalid:", form.errors)
    else:
        form = HealthReportForm()

    return render(request, 'main/reguser_dashboard.html', {'form': form})



def forgot_view(request):
   return render(request, 'main/partials/forgot.html')

@login_required(login_url='livora')
@user_passes_test(is_regular_user, login_url='livora')
def ruser_comp(request, component_name):
    template_path = f"main/ruser_comp/{component_name}.html"
    context = {}
    announcements = NurseAnnouncement.objects.order_by('-created_at')[:5]
    context['nurse_announcements'] = announcements
    if component_name == 'rqst_his_std':
        reports = HealthReport.objects.filter(user=request.user).order_by('-created_at')
        print(f"Fetched {reports.count()} reports for user: {request.user}")
        context['health_reports'] = reports
    try:
        print(f"Trying to render: {template_path}")
        return render(request, template_path, context)
    except TemplateDoesNotExist:
        print(f"Template does NOT exist: {template_path}")
        return HttpResponse(f"Template {template_path} not found", status=404)


import json

@require_POST
@login_required
@user_passes_test(is_admin)
def update_nurse_status(request):
    try:
        data = json.loads(request.body)
        status = data.get('status', 'closed')
        if status not in ['open', 'closed']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
            
        cache.set('nurse_status', status, timeout=None)
        return JsonResponse({'success': True, 'status': status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



def get_nurse_status(request):
   status = cache.get('nurse_status', 'closed')
   return JsonResponse({'status': status})


def student_dashboard_view(request):
    status = cache.get('nurse_status', 'closed')
    return render(request, 'main/student_dashboard.html', {
        'office_status': status,
        'is_admin': False
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if request.method == "POST":
        if 'add_note' in request.POST:
            message = request.POST.get('note')
            if message:
                NurseAnnouncement.objects.create(message=message)
        elif 'delete_note' in request.POST:
            note_id = request.POST.get('delete_note')
            NurseAnnouncement.objects.filter(id=note_id).delete()

    announcements = NurseAnnouncement.objects.order_by('-created_at')
    status = cache.get('nurse_status', 'closed')
    return render(request, 'main/admin_dashboard.html', {
        'nurse_announcements': announcements,
        'office_status': status,
        'is_admin': True
    })

@login_required
@user_passes_test(is_admin)
def admin_comp(request, component_name):
    context = {
        'nurse_announcements': NurseAnnouncement.objects.order_by('-created_at'),
        'office_status': cache.get('nurse_status', 'closed'),
        'is_admin': True
    }
    return render(request, f'main/admin_comp/{component_name}.html', context)

def custom_logout(request):
    was_staff = request.user.is_staff
    logout(request)
    if was_staff:
        return redirect('nurse_login')
    return redirect('livora')


@login_required
@user_passes_test(is_admin)
def get_student_list(request):
    try:
        # API key in settings
        payload = {
            'key': settings.API_KEY,
        }
        response = requests.get('https://api.ksain.net/v1/students.php', data=payload)
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        return JsonResponse({'error': 'Failed to fetch student list'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def get_student_details(request, student_id):
    try:
        payload = {
            'key': settings.API_KEY,
            'student_id': student_id
        }
        response = requests.get('https://api.ksain.net/v1/student-details.php', data=payload)
        health_reports = HealthReport.objects.filter(student_id=student_id).order_by('-created_at')
        
        if response.status_code == 200:
            student_data = response.json()
            student_data['health_reports'] = list(health_reports.values())
            return JsonResponse(student_data)
        return JsonResponse({'error': 'Failed to fetch student details'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)