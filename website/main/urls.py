from django.urls import path
from main import views
from . import views

urlpatterns = [
    path('', views.home, name='livora'),  # Default route for student login
    path('nurse/', views.nurse_login, name='nurse_login'),  # Nurse login at /nurse/
    path('forgot-box/', views.forgot_view, name='forgot_box'),
    path('register-box/', views.register_box, name='register_box'),
    path('login-box/', views.login_box, name='login_box'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.reguser_dashboard, name='reguser_dashboard'),
    path('logout/', views.custom_logout, name='logout'),
    path('ruser-comp/<str:component_name>/', views.ruser_comp, name='ruser_comp'),
    path('admin-comp/<str:component_name>/', views.admin_comp, name='admin_comp'),
    path('update-nurse-status/', views.update_nurse_status, name='update_nurse_status'),
    path('get-nurse-status/', views.get_nurse_status, name='get_nurse_status'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('submit-health-report/', views.submit_health_report, name='submit_health_report'),
    path('request-history/', views.request_history, name='request_history'),
    # New API endpoints for student info
    path('api/students/', views.get_student_list, name='get_student_list'),
    path('api/student/<str:student_id>/', views.get_student_details, name='get_student_details'),
]

