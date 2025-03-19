from rest_framework import viewsets, generics
from ..models import Offer, OfferDetail, Order, Review
from .serializers import OfferSerializer, OfferDetailSerializer, OrderSerializer, UserSerializer, CustomUser, CustomerUserSerializer, BusinessUserSerializer, RegistrationSerializer, ReviewSerializer, ReviewDetailSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate


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

    def perform_create(self, serializer):
        # Setze den eingeloggten User als 'customer_user'
        customer_user = self.request.user

        # Hole die OfferDetail-Instanz über die offer_detail_id
        offer_detail = serializer.validated_data.pop('offer_detail')

        # Erstelle die Order mit den OfferDetail-Daten
        serializer.save(
            customer_user=customer_user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            business_user=offer_detail.owner,
            status='in_progress'  # Falls nötig, Standardstatus setzen
        )


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


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            # Token erstellen oder abrufen
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": username, "email": user.email, "user_id": user.pk}, status=status.HTTP_200_OK)
        return Response({"detail": ["Falsche Anmeldedaten."]}, status=status.HTTP_401_UNAUTHORIZED)


class RegistrationView(APIView):

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account)
            data = {
                'token': token.key,
                'username': saved_account.username,
                'email': saved_account.email,
                "user_id": saved_account.pk
            }

        else:
            data = serializer.errors

        return Response(data)


class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewSerializer
        elif self.action == 'update':
            return ReviewDetailSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(reviewer=self.request.user)
        return Response(serializer.data)
