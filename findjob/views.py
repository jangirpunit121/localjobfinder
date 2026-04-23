from django.shortcuts import render,get_object_or_404
from .models import * 
# Create your views here.
from django.contrib.auth import login,logout,authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, CandidateProfile
from django.contrib.auth.decorators import login_required
from django.db.models import Count   
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Application
import json


def user_signup(request):
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        skills = request.POST.get('skills')
        location = request.POST.get('location')
        resume = request.FILES.get('resume')  # file upload

        # Validation
        if not all([full_name, email, password, phone, qualification, experience, skills, location]):
            messages.error(request, 'All fields are required.')
            return render(request, 'user_signup.html')

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'user_signup.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already used.')
            return render(request, 'user_signup.html')

        # Create User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name.split()[0] if ' ' in full_name else full_name,
            last_name=full_name.split()[-1] if len(full_name.split()) > 1 else '',
            user_type='candidate',
            mobile_number=phone
        )

        # Create Candidate Profile
        candidate_profile = CandidateProfile.objects.create(
            user=user,
            qualification=qualification,
            experience=experience,
            skills=skills,
            location=location,
            resume=resume
        )

        # Log the user in
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('user-dashboard')

    return render(request, 'user_signup.html')
    

def user_login(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        
        user=authenticate(request,username=email,password=password)
        if user is not None:
            login(request,user)
            return redirect('user-dashboard')
        else:
            messages.error(request,'Invalid Credentials')
    return render(request,'user_login.html')

def company_signup(request):
    if request.method == 'POST':
        # User fields
        
        email = request.POST['email']
        password = request.POST['password']
        mobile_number = request.POST['mobile_number']
        
        # CompanyProfile fields
        company_name = request.POST['company_name']
        website = request.POST.get('website', '')
        location = request.POST['location']
        description = request.POST['description']
        contact_number = request.POST.get('contact_number', '')
        logo = request.FILES.get('logo')
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            user_type='company',
            mobile_number=mobile_number
        )
        
        # Create company profile
        CompanyProfile.objects.create(
            user=user,
            company_name=company_name,
            website=website,
            location=location,
            description=description,
            contact_number=contact_number,
            logo=logo
        )
        
        # Auto login
        login(request, user)
        return redirect('company-dashboard')  # apna URL naam daalo
    
    return render(request, 'company_signup.html')


def company_login(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        
        user=authenticate(request,username=email,password=password)
        if user is not None:
            login(request,user)
            return redirect('company-dashboard')
        else:
            messages.error(request,'Invalid Credentials')
    return render(request,'company_login.html')
    
    



from django.db.models import Q

def user_dashboard(request):
    # 1. GET parameters lo
    selected_category = request.GET.get('category', '')
    city = request.GET.get('city', '').strip()
    district = request.GET.get('district', '').strip()
    
    # 2. Base queryset (active jobs only, maan lo)
    jobs = Job.objects.filter(is_active=True)  # agar active flag hai to
    
    # 3. Category filter
    if selected_category:
        jobs = jobs.filter(category__iexact=selected_category)
    
    # 4. Location filter: city AUR district dono se (OR condition)
    # Jab city ho ya district ho, to location field mein se koi match kare
    location_filters = Q()
    if city and city != 'Unknown':
        location_filters |= Q(location__icontains=city)
    if district and district != 'Unknown':
        location_filters |= Q(location__icontains=district)
    
    if location_filters:  # agar koi bhi location filter hai to apply karo
        jobs = jobs.filter(location_filters)
    
    # 5. Categories list (distinct, not empty)
    categories = Job.objects.filter(is_active=True).values_list('category', flat=True).distinct().exclude(category__isnull=True).exclude(category='')
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'selected_category': selected_category,
        'city': city,
        'district': district,
    }
    return render(request, 'user_dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('user_login')


def home(request):
    return render(request,'home.html')



def add_job(request):
    # 1. Check if user is logged in
    if not request.user.is_authenticated:
        return redirect('company_login')
    
    
    try:
        company = request.user.companyprofile  
    except CompanyProfile.DoesNotExist:
        
        return redirect('company-login')
    
    if request.method == 'POST':
        job = Job.objects.create(
            company=company,
            title=request.POST['title'],
            description=request.POST['description'],
            location=request.POST['location'],
            salary=request.POST.get('salary', ''),
            job_type=request.POST['job_type'],
            category=request.POST['category'],
        )
        return redirect('company-dashboard')  # ya 'company_dashboard'
    
    return render(request, 'add_job.html')



def job_details(request,job_id):
    if not request.user.is_authenticated:
        return redirect('user-login')
    
    jobs=get_object_or_404(Job,id=job_id)
    
    return render(request,'job_detail.html',{'job':jobs})



@login_required(login_url='user-login')
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Only POST requests allowed
    if request.method != 'POST':
        messages.info(request, "Please use the apply button.")
        return redirect('job_detail', job_id=job.id)
    
    # Try to get candidate from session first
    candidate_id = request.session.get('candidate_id')
    candidate = None
    
    if candidate_id:
        try:
            candidate = CandidateProfile.objects.get(id=candidate_id)
        except CandidateProfile.DoesNotExist:
            candidate = None
    
    # Fallback: use request.user
    if not candidate and request.user.is_authenticated:
        if hasattr(request.user, 'candidateprofile'):
            candidate = request.user.candidateprofile
            # Also fix session
            request.session['candidate_id'] = candidate.id
            request.session.save()
    
    if not candidate:
        messages.error(request, "Candidate profile not found. Please complete your profile.")
        return redirect('candidate_profile_edit')  # change to your profile edit URL
    
    # Check if already applied
    if Application.objects.filter(job=job, candidate=candidate).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_detail', job_id=job.id)
    
    # Create application
    cover_letter = request.POST.get('cover_letter', '').strip()
    Application.objects.create(
        job=job,
        candidate=candidate,
        cover_letter=cover_letter or None,
        status='pending'
    )
    
    messages.success(request, f"Successfully applied for '{job.title}'!")
    return redirect('user-dashboard')


@login_required(login_url='company-login')


def company_dashboard(request):
    # Ensure user is a company
    if request.user.user_type != 'company':
        # Redirect or error
        from django.shortcuts import redirect
        return redirect('user-dashboard')
    
    # Get logged-in company profile
    company = request.user.companyprofile
    
    # Jobs posted by this company only
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    
    # Total jobs count
    total_jobs = jobs.count()
    
    # Applications for this company's jobs (via job__company)
    applications = Application.objects.filter(job__company=company)
    total_applications = applications.count()
    
    # Application status counts for this company
    pending_applications = applications.filter(status='pending').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Unique candidates who applied to this company's jobs
    candidates_with_counts = CandidateProfile.objects.filter(
        application__job__company=company
    ).annotate(
        application_count=Count('application')
    ).select_related('user').order_by('-application_count')
    
    total_candidates = candidates_with_counts.count()
    
    # Recent applications for this company (latest 10)
    recent_applications = applications.select_related(
        'job', 'candidate__user'
    ).order_by('-applied_at')[:10]
    
    # Recent jobs (latest 5)
    recent_jobs = jobs[:5]
    
    context = {
        'company': company,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'total_candidates': total_candidates,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'recent_applications': recent_applications,
        'recent_jobs': recent_jobs,
        'candidates_with_counts': candidates_with_counts,
    }
    return render(request, 'admin_dashboard.html', context)




@login_required
def edit_profile(request):
    user = request.user
    
    # For company users
    if user.user_type == 'company':
        profile = user.companyprofile
        
        if request.method == 'POST':
            # Update User fields
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.mobile_number = request.POST.get('mobile_number')
            user.save()
            
            # Update CompanyProfile fields
            profile.company_name = request.POST.get('company_name')
            profile.location = request.POST.get('location')
            profile.website = request.POST.get('website')
            profile.contact_number = request.POST.get('contact_number')
            profile.description = request.POST.get('description')
            
            if request.FILES.get('logo'):
                profile.logo = request.FILES['logo']
            
            profile.save()
            messages.success(request, "Company profile updated successfully!")
            return redirect('company-dashboard')
        
        context = {
            'user': user,
            'profile': profile,
            'user_type': 'company'
        }
        return render(request, 'edit_profile.html', context)
    
    # For candidate users
    elif user.user_type == 'candidate':
        profile = user.candidateprofile
        
        if request.method == 'POST':
            # Update User fields
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.mobile_number = request.POST.get('mobile_number')
            user.save()
            
            # Update CandidateProfile fields
            profile.skills = request.POST.get('skills')
            profile.experience = request.POST.get('experience')
            profile.location = request.POST.get('location')
            profile.qualification = request.POST.get('qualification')
            
            if request.FILES.get('resume'):
                profile.resume = request.FILES['resume']
            
            profile.save()
            messages.success(request, "Candidate profile updated successfully!")
            return redirect('user-dashboard')
        
        context = {
            'user': user,
            'profile': profile,
            'user_type': 'candidate'
        }
        return render(request, 'edit_profile.html', context)
    
    else:
        messages.error(request, "Invalid user type.")
        return redirect('home') 
    
    
    
def edit_job(request,job_id):
    job=get_object_or_404(Job,id=job_id)
    if request.method=="POST":
        job.title=request.POST.get('title')
        job.description=request.POST.get('description')
        job.location=request.POST.get('location')
        job.salary=request.POST.get('salary')
        job.job_type=request.POST.get('job_type')
        job.category=request.POST.get('category')
        job.save()
        return redirect('company-dashboard')
    return render(request,'edit_job.html',{'job':job})


def delete_job(request,job_id):
    job=get_object_or_404(Job,id=job_id)
    job.delete()
    return redirect('company-dashboard')

def candidate_detail(request,candidate_id):
    candidate=CandidateProfile.objects.get(id=candidate_id)
    return render(request,'admin_candidate_detail.html',{'candidate':candidate})


# ✅ CORRECT - returns all applications for the candidate
def candidate_applications(request, candidate_id):
    from .models import CandidateProfile  # adjust import as needed
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)
    applications = candidate.application_set.all().select_related('job', 'job__company')
    return render(request, 'admin_candidate_applications.html', {
        'candidate': candidate,
        'applications': applications,  # ← This is a QuerySet (iterable)
        'pending_count': applications.filter(status='pending').count(),
        'accepted_count': applications.filter(status='accepted').count(),
    })
    
@csrf_exempt
@require_http_methods(["POST"])
def update_application_status(request, app_id):
    try:
        application = Application.objects.get(id=app_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in ['pending', 'accepted', 'rejected']:
            application.status = new_status
            application.save()
            return JsonResponse({'success': True, 'status': new_status})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
