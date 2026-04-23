from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',home,name='home-page'),
    path('user-signup/',user_signup,name='user_signup'),
    path('user-login/',user_login,name='user_login'),
    path('company-login/',company_login,name='company-login'),
    path('company-signup',company_signup,name='company-signup'),
    path('user-dashboard/',user_dashboard,name='user-dashboard'),
    path('logout-session/',logout_view,name='abcd'),
    path('company-dashboard/',company_dashboard,name='company-dashboard'),
    path('company-dashboard/add-job',add_job,name='add-job'),
    path('job-detail/<int:job_id>/',job_details,name='job_detail'),
    # urls.py
path('apply/<int:job_id>/', apply_job, name='apply_job'),
path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
path('edit-profile/', edit_profile, name='edit_profile'),
path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
path('candidate-detail/<int:candidate_id>/', candidate_detail, name='candidate-detail'),
path('candidate-applications/<int:candidate_id>/', candidate_applications, name='candidate-applications'),
path('application/<int:app_id>/update-status/', update_application_status, name='update_application_status'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)