from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from ..models import Offer, OfferDetail, Order
from .serializers import OfferSerializer, OfferDetailSerializer, OrderSerializer, UserSerializer, CustomUser, CustomerUserSerializer, BusinessUserSerializer
from rest_framework.response import Response
from rest_framework import status


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        offer = self.get_object()  # Holt die Offer-Instanz basierend auf pk
        user = offer.user  # Verknüpfter User des Angebots

     # Serialisierte Offer-Daten
        offer_data = OfferSerializer(offer).data

        # Ergänzte User-Daten
        offer_data["user_details"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
        }

        return Response(offer_data)


class OfferDetailViewSet(viewsets.ModelViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()  # Holt die Order-Instanz
        serializer = self.get_serializer(order)  # Serialisiert die Instanz

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(
            order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class OrderCountViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        business_user = CustomUser.objects.filter(pk=pk).first()

        if not business_user:
            return Response({"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)

        order_count = Order.objects.filter(
            business_user=business_user, status='in_progress'
        ).count()

        return Response({"order_count": order_count})


class CompletedOrderCountViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):

        business_user = CustomUser.objects.filter(pk=pk).first()
        if not business_user:
            return Response({"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)

        order_count = Order.objects.filter(
            business_user=business_user, status='completed'
        ).count()

        return Response({"completed_order_count": order_count})


class ProfilViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


class ProfilTypeViewSet(generics.ListCreateAPIView):
    def get_serializer_class(self):
        user_type = self.kwargs.get('user_type', None)
        if user_type == 'business':
            return BusinessUserSerializer
        elif user_type == 'customer':
            return CustomerUserSerializer
        return BusinessUserSerializer

    def get_queryset(self):
        user_type = self.kwargs.get('user_type', None)
        if user_type in ['business', 'customer']:
            return CustomUser.objects.filter(type=user_type)
        return CustomUser.objects.none()
