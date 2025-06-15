from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.views.decorators.http import require_POST
from django.db import transaction
from datetime import datetime, date
from django.core.paginator import Paginator
import requests, json
from django.http import JsonResponse
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import csv
from io import StringIO
from .models import HealthReport, NurseStatus, NurseAnnouncement, MedicalHistory,UserProfile
from .forms import HealthReportForm,MedicalHistoryForm
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request,'main/livora.html')

def nurse_login(request):
    if request.method=='POST':
        form = AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            if user.is_staff:
                login(request,user)
                return redirect('admin_dashboard')
            else:
                messages.error(request,"You don't have admin privileges.")
                return redirect('nurse_login')
    else:
        form=AuthenticationForm()
    return render(request,'main/nurse_login.html',{'form': form})

def login_box(request):
   form=AuthenticationForm()
   return render(request,'main/partials/login.html',{'form':form})


def register_box(request):
   form=UserCreationForm()
   return render(request,'main/partials/register.html',{'form':form})


def register(request):
   if request.method=='POST':
       form=UserCreationForm(request.POST)
       if form.is_valid():
           form.save()
           return redirect('login')
   else:
       form=UserCreationForm()
   return render(request,'main/register.html',{'form':form})

#login_view with API 
def login_view(request):
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')

        payload={
            'key': settings.API_KEY,
            'username':username,
            'password':password,
        }

        response=requests.post('https://api.ksain.net/v1/login.php',data=payload)
        if response.status_code==200:
            res=response.json()
            if res.get('status')=='success':
                student_data=res.get('data',{})
                name=student_data.get('name','')
                first_name=name.split()[0] if name else ''
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''

                user, created=User.objects.get_or_create(username=username)
                user.first_name=first_name
                user.last_name=last_name
                user.save()
                login(request,user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('reguser_dashboard')
            else:
                messages.error(request,res.get('message','Login failed.'))
        else:
            messages.error(request,"Failed to contact login API.")

    return render(request,'main/livora.html')


def C_Logout_View(request):
   logout(request)
   return redirect('livora')


def is_admin(user):
   return user.is_authenticated and user.is_staff


def is_regular_user(user):
   return user.is_authenticated and not user.is_staff

def request_history(request):
    print("Current user:",request.user.username)
    reports=HealthReport.objects.filter(user=request.user).order_by('-created_at')
    print(f"Reports count for {request.user}:{reports.count()}")
    return render(request,'main/ruser_comp/rqst_his_std.html',{'health_reports':reports})


def reguser_dashboard(request):
   return render(request,'dashboard.html')


@login_required(login_url='login')
@user_passes_test(is_regular_user, login_url='livora')
def reguser_dashboard(request):
   if request.method=='POST':
       form=HealthReportForm(request.POST,request.FILES)
       if form.is_valid():
           report=form.save(commit=False)
           report.save()
           return redirect('reguser_dashboard')
   else:
       form=HealthReportForm()
   return render(request,'main/reguser_dashboard.html',{'form':form})


@login_required(login_url='login')
@user_passes_test(is_regular_user, login_url='livora')
def submit_health_report(request):
    if request.method=='POST':
        user=request.user
        data=request.POST.copy()
        symptoms_raw=data.get('symptoms', '')
        symptoms_list=[s.strip().lower() for s in symptoms_raw.split(',') if s.strip()]
        data.setlist('symptoms',symptoms_list)

        form=HealthReportForm(data)
        if form.is_valid():
            report=form.save(commit=False)
            report.user=user
            report.save()
            return redirect('reguser_dashboard')
        else:
            print("Form invalid:",form.errors)
    else:
        form=HealthReportForm()

    return render(request,'main/reguser_dashboard.html',{'form':form})



def forgot_view(request):
   return render(request,'main/partials/forgot.html')

@login_required(login_url='livora')
@user_passes_test(is_regular_user, login_url='livora')
def ruser_comp(request,component_name):
    template_path=f"main/ruser_comp/{component_name}.html"
    context={}
    announcements=NurseAnnouncement.objects.order_by('-created_at')[:5]
    context['nurse_announcements']=announcements
    if component_name=='rqst_his_std':
        reports=HealthReport.objects.filter(user=request.user).order_by('-created_at')
        print(f"Fetched {reports.count()} reports for user: {request.user}")
        context['health_reports']=reports
    try:
        print(f"Trying to render:{template_path}")
        return render(request,template_path,context)
    except TemplateDoesNotExist:
        print(f"Template does NOT exist:{template_path}")
        return HttpResponse(f"Template {template_path} not found",status=404)

@require_POST
@login_required
@user_passes_test(is_admin)
def update_nurse_status(request):
    try:
        data=json.loads(request.body)
        status=data.get('status','closed')
        if status not in ['open','closed']:
            return JsonResponse({'success':False,'error':'Invalid status'},status=400)
            
        cache.set('nurse_status',status,timeout=None)
        return JsonResponse({'success':True, 'status':status})
    except Exception as e:
        return JsonResponse({'success':False, 'error':str(e)},status=400)

def get_nurse_status(request):
   status=cache.get('nurse_status', 'closed')
   return JsonResponse({'status':status})


def student_dashboard_view(request):
    status=cache.get('nurse_status', 'closed')
    return render(request,'main/student_dashboard.html', {
        'office_status':status,
        'is_admin':False
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if request.method=="POST":
        if 'add_note' in request.POST:
            message=request.POST.get('note')
            if message:
                NurseAnnouncement.objects.create(message=message)
        elif 'delete_note' in request.POST:
            note_id=request.POST.get('delete_note')
            NurseAnnouncement.objects.filter(id=note_id).delete()

    announcements=NurseAnnouncement.objects.order_by('-created_at')
    status=cache.get('nurse_status', 'closed')
    return render(request,'main/admin_dashboard.html', {
        'nurse_announcements':announcements,
        'office_status':status,
        'is_admin':True
    })


@login_required
@user_passes_test(is_admin)
def admin_comp(request, component_name):
    context={
        'nurse_announcements':NurseAnnouncement.objects.order_by('-created_at'),
        'office_status':cache.get('nurse_status', 'closed'),
        'is_admin':True
    }
    
    if component_name=='admin_history':
        print("Loading admin history")
        page=request.GET.get('page', 1)
        reports_per_page=10  
        reports=HealthReport.objects.all().order_by('-created_at')
        
        months=[]
        current_date=datetime.now()
        for i in range(12):
            if i==0:
                date=current_date.replace(day=1)
            else:
                if current_date.month-i>0:
                    date=current_date.replace(day=1,month=current_date.month-i)
                else:
                    year_diff=((i-current_date.month)//12)+1
                    month=current_date.month-i+(12*year_diff)
                    date=current_date.replace(day=1,month=month,year=current_date.year-year_diff)
            
            months.append({
                'value':date.strftime('%Y-%m'),
                'label':date.strftime('%B %Y')
            })
        context['months']=months
        
    
        unviewed_count=reports.filter(nurse_viewed=False).count()
        context['unviewed_count']=unviewed_count
        paginator=Paginator(reports,reports_per_page)
        try:
            reports_page=paginator.page(page)
        except:
            reports_page=paginator.page(1)
            
        print(f"Found {reports.count()} reports, showing page {page}")
        context['health_reports']=reports_page
        context['page_obj']=reports_page
        context['total_pages']=paginator.num_pages
    
    return render(request,f'main/admin_comp/{component_name}.html',context)


def custom_logout(request):
    was_staff=request.user.is_staff
    logout(request)
    if was_staff:
        return redirect('nurse_login')
    return redirect('livora')

def mark_report_viewed(request,report_id):
    try:
        report=get_object_or_404(HealthReport,id=report_id)
        print(f"Marking report {report_id} as viewed")  
        report.nurse_viewed=True
        report.save()
        return JsonResponse({'status':'success'})
    except Exception as e:
        print(f"Error marking report as viewed:{str(e)}")  
        return JsonResponse({'status':'error','message': str(e)},status=400)


@login_required
@user_passes_test(is_admin)
def get_student_list(request):
    try:
        
        payload={
            'key':settings.API_KEY,
        }
        response=requests.get('https://api.ksain.net/v1/students.php', data=payload)
        
        if response.status_code==200:
            return JsonResponse(response.json())
        return JsonResponse({'error':'Failed to fetch student list'}, status=400)
    except Exception as e:
        return JsonResponse({'error':str(e)},status=500)

@login_required
@user_passes_test(is_admin)
def get_student_details(request):
    name=request.GET.get('name')
    if not name:
        return JsonResponse({'error':'Name parameter is required'}, status=400)

    response=requests.post(
        'https://api.ksain.net/v1/studentID.php',
        data={
            'key':settings.API_KEY,
            'name':name
        }
    )

    if response.status_code!=200:
        return JsonResponse({'error':'Failed to reach student API'}, status=response.status_code)

    res_json=response.json()
    if res_json.get('code')!=200:
        return JsonResponse({'error':res_json.get('message', 'Student not found')}, status=400)

    matched_students=res_json.get('data',[])
    results=[]

    for student in matched_students:
        student_id=student.get('studentID')
        batch=student.get('batch')
        user=None
        try:
            user=User.objects.get(userprofile__student_id=student_id)
        except User.DoesNotExist:
            try:
                user=User.objects.get(username__iexact=name)
            except User.DoesNotExist:
                user=None
            if user:
                try:
                    profile=user.userprofile
                except UserProfile.DoesNotExist:
                    profile=None
                if not profile:
                    with transaction.atomic():
                        profile=UserProfile.objects.create(user=user,student_id=student_id)
                elif profile.student_id!=student_id:
                    profile.student_id=student_id
                    profile.save()

        if not user:
            continue  
        health_reports=HealthReport.objects.filter(user=user).order_by('-created_at').values()

        try:
            med=MedicalHistory.objects.get(user=user)
            medical_history_data={
                'dob': med.dob,
                'sex': med.sex,
                'allergies': med.allergies,
                'other_issues': med.other_issues,
                'insurance': med.insurance,
                'insurance_start': med.insurance_start,
                'insurance_end': med.insurance_end,
            }
        except MedicalHistory.DoesNotExist:
            medical_history_data={}

        results.append({
            'studentID':student_id,
            'batch':batch,
            'full_name':f"{user.first_name} {user.last_name}",
            'health_reports': list(health_reports),
            'medical_history': medical_history_data,
        })

    return JsonResponse({'results':results})

    

def save_nurse_comment(request,report_id):
    if request.method=='POST':
        try:
            data=json.loads(request.body)
            comment=data.get('nurse_comment','')
            report=HealthReport.objects.get(id=report_id)
            report.nurse_comment=comment
            report.save()
            return JsonResponse({'status':'success'})
        except HealthReport.DoesNotExist:
            return JsonResponse({'status':'error','message':'Report not found'},status=404)
    return JsonResponse({'status':'error','message':'Invalid request'},status=400)

def admin_report_detail(request,report_id):
    report=get_object_or_404(HealthReport,id=report_id)
    return render(request,'main/admin_comp/admin_dtld_window.html',{'report':report})

@login_required
@user_passes_test(is_admin)
def admin_dtld_window(request,report_id):
    report=get_object_or_404(HealthReport,id=report_id)
    context={
        'report':report,
        'nurse_announcements':NurseAnnouncement.objects.order_by('-created_at'),
        'office_status':cache.get('nurse_status', 'closed'),
        'is_admin':True
    }
    return render(request,'main/admin_comp/admin_dtld_window.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_star(request, report_id):
    try:
        report=get_object_or_404(HealthReport, id=report_id)
        report.starred=not report.starred
        report.save()
        return JsonResponse({'status':'success','starred':report.starred})
    except Exception as e:
        return JsonResponse({'status':'error','message':str(e)},status=400)
    
@login_required
@user_passes_test(is_admin)
def monthly_report(request,year_month):
    if not request.user.is_staff: 
        return HttpResponse('Unauthorized',status=401)
    reports=HealthReport.objects.all()
    if year_month!='all':
        year=int(year_month[:4])
        month=int(year_month[5:7])
        start_date=datetime(year,month,1)
        if month==12:
            end_date=datetime(year+1,1,1)
        else:
            end_date=datetime(year,month+1,1)
            
        reports=reports.filter(created_at__gte=start_date,created_at__lt=end_date)
    reports=reports.order_by('-created_at')

    response=HttpResponse(content_type='text/csv')
    filename='health_reports.csv' if year_month=='all' else f'health_reports_{year_month}.csv'
    response['Content-Disposition']=f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['Date Submitted','Student Name','Symptoms','Duration (days)'])
    for report in reports:
        symptoms=report.symptoms.strip('[]\'').replace('\'', '').replace(',', ', ')
        writer.writerow([
            report.created_at.strftime('%Y-%m-%d %H:%M'),
            report.user.get_full_name(),
            symptoms,
            report.duration
        ])
    return response
    
def upload_medical_history(request):
    if request.method == 'POST':
        print("HIT VIEW: POST")

        user=request.user

        # Get values from POST
        dob=request.POST.get('dob')
        sex=request.POST.get('sex')
        allergies=request.POST.get('allergies')
        other_issues=request.POST.get('otherIssues')
        insurance=request.POST.get('insurance')
        insurance_start=request.POST.get('insuranceStart')
        insurance_end=request.POST.get('insuranceEnd')

        emergency_name=request.POST.get('emergency_name')
        emergency_relationship=request.POST.get('emergency_relationship')
        emergency_phone=request.POST.get('emergency_phone')

        clinic_name=request.POST.get('clinic_name')
        doctor_name=request.POST.get('doctor_name')
        clinic_phone=request.POST.get('clinic_phone')
        clinic_address=request.POST.get('clinic_address')
        clinic_reason=request.POST.get('clinic_reason')

        medical_history,created=MedicalHistory.objects.get_or_create(user=user)
        medical_history.dob=dob or None
        medical_history.sex=sex or ""
        medical_history.allergies=allergies or ""
        medical_history.other_issues=other_issues or ""
        medical_history.insurance=insurance or ""
        medical_history.insurance_start=insurance_start or None
        medical_history.insurance_end=insurance_end or None

        medical_history.emergency_name=emergency_name or ""
        medical_history.emergency_relationship=emergency_relationship or ""
        medical_history.emergency_phone=emergency_phone or ""

        medical_history.clinic_name=clinic_name or ""
        medical_history.doctor_name=doctor_name or ""
        medical_history.clinic_phone=clinic_phone or ""
        medical_history.clinic_address=clinic_address or ""
        medical_history.clinic_reason=clinic_reason or ""
        medical_history.save()
        print("Saved object:", vars(medical_history))

        return JsonResponse({'success':True})
    return JsonResponse({'success':True})

def medical_history_page(request):
    user=request.user
    medical_history,created=MedicalHistory.objects.get_or_create(user=user)

    return render(request, 'med_his_std.html', {
        'medical_history': medical_history,
        'surgeries':medical_history.surgeries.all()
    })

