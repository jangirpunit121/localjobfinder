from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'company-profiles', CompanyProfileViewSet)
router.register(r'candidate-profiles', CandidateProfileViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'applications', ApplicationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),  # for login/logout in browsable API
]