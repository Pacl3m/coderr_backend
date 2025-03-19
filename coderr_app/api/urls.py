from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfferViewSet, OfferDetailViewSet, OrderViewSet, OrderCountViewSet, CompletedOrderCountViewSet, ProfilViewSet, ProfilTypeViewSet

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offers')
router.register(r'offerdetails', OfferDetailViewSet, basename='offerdetails')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'order-count', OrderCountViewSet, basename='order-count')
router.register(r'completed-order-count',
                CompletedOrderCountViewSet, basename='completed-order-count')
router.register(r'profile', ProfilViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('profiles/<str:user_type>/',
         ProfilTypeViewSet.as_view(), name='profilType-detail'),
    # path('answers/<int:pk>/', AnswerDetailView.as_view(), name='answer-detail'),
]
