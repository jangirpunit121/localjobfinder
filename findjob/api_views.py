from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .models import *
from .serializers import *
from django.db.models import Q

User = get_user_model()

# ==============================
# Custom Permissions
# ==============================

class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (hasattr(request.user, 'companyprofile') and 
                obj.company == request.user.companyprofile)

class IsCandidateOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'candidateprofile') and obj == request.user.candidateprofile

class IsApplicationAccessible(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            if hasattr(request.user, 'candidateprofile'):
                return obj.candidate == request.user.candidateprofile
            if hasattr(request.user, 'companyprofile'):
                return obj.job.company == request.user.companyprofile
            return False
        return request.method == 'DELETE' and hasattr(request.user, 'candidateprofile') and obj.candidate == request.user.candidateprofile

# ==============================
# User ViewSet (with token auth)
# ==============================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  # only admin can list users
    authentication_classes = [TokenAuthentication]   # ✅ No SessionAuthentication

    @decorators.action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def signup(self, request):
        data = request.data.copy()
        password = data.get('password')
        if not password:
            return Response({'error': 'Password required'}, status=status.HTTP_400_BAD_REQUEST)
        data['password'] = make_password(password)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'username': user.username
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @decorators.action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'})

    @decorators.action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        token = Token.objects.get(user=request.user)
        return Response({
            'token': token.key,
            'username': request.user.username
        })

# ==============================
# CompanyProfile ViewSet
# ==============================

class CompanyProfileViewSet(viewsets.ModelViewSet):
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CompanyProfile.objects.all()
        return CompanyProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ==============================
# CandidateProfile ViewSet
# ==============================

class CandidateProfileViewSet(viewsets.ModelViewSet):
    queryset = CandidateProfile.objects.all()
    serializer_class = CandidateProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsCandidateOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CandidateProfile.objects.all()
        return CandidateProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ==============================
# Job ViewSet
# ==============================





class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # 🔥 frontend se location aayegi
        location = self.request.query_params.get('location')

        print("Frontend Location:", location)

        # ✅ Admin
        if user.is_staff:
            return Job.objects.all()

        # ✅ Company
        if hasattr(user, 'companyprofile'):
            return Job.objects.filter(company=user.companyprofile)

        # ✅ Candidate / Normal user
        if location:
            location = location.strip().lower()

            return Job.objects.filter(
                location__icontains=location
            )

        # ❗ agar location nahi bheji frontend ne
        return Job.objects.none()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCompanyOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, 'companyprofile'):
            serializer.save(company=user.companyprofile)
        else:
            raise PermissionError("Only companies can create jobs")
    
# ==============================
# Application ViewSet
# ==============================

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Application.objects.all()
        if hasattr(user, 'candidateprofile'):
            return Application.objects.filter(candidate=user.candidateprofile)
        if hasattr(user, 'companyprofile'):
            return Application.objects.filter(job__company=user.companyprofile)
        return Application.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsApplicationAccessible()]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'candidateprofile'):
            raise PermissionError("Only candidates can apply for jobs")
        job_id = self.request.data.get('job')
        if Application.objects.filter(candidate=user.candidateprofile, job_id=job_id).exists():
            raise PermissionError("You have already applied for this job")
        serializer.save(candidate=user.candidateprofile)