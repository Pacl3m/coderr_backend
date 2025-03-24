from rest_framework import viewsets, generics
from ..models import Offer, OfferDetail, Order, Review
from .serializers import OfferSerializer, OfferDetailSerializer, OrderSerializer, UserSerializer, CustomUser, CustomerUserSerializer, BusinessUserSerializer, RegistrationSerializer, ReviewSerializer, ReviewDetailSerializer, OrderDetailSerializer
from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from .permissions import IsOwnerOrAdmin, IsBusinessUser, IsSuperUser, IsOwnUserOrAdmin, IsAuthenticatedCustom
from rest_framework.pagination import LimitOffsetPagination


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 3
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsBusinessUser, IsOwnerOrAdmin]
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        queryset = Offer.objects.all()

        creator_id_param = self.request.query_params.get('creator_id', None)
        if creator_id_param is not None:
            queryset = queryset.filter(user__id=creator_id_param)

        min_price_param = self.request.query_params.get('min_price', None)
        if min_price_param is not None:
            queryset = self.filter_by_min_price(queryset, min_price_param)

        # Filter nach min_delivery_time, falls vorhanden, aber berechnete Felder
        max_delivery_time_param = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time_param is not None:
            queryset = self.filter_by_max_delivery_time(queryset, max_delivery_time_param)
        return queryset

    def filter_by_min_price(self, queryset, min_price_param):
        # Filtern der Angebote nach min_price basierend auf Details-Daten
        filtered_queryset = []
        for offer in queryset:
            min_price = min(detail.price for detail in offer.details.all()) if offer.details.exists() else None
            if min_price is not None and min_price <= float(min_price_param):
                filtered_queryset.append(offer)
        return filtered_queryset

    def filter_by_max_delivery_time(self, queryset, max_delivery_time_param):
        # Filtern der Angebote nach min_delivery_time basierend auf Details-Daten
        filtered_queryset = []
        for offer in queryset:
            max_delivery_time = min(detail.delivery_time_in_days for detail in offer.details.all()) if offer.details.exists() else None
            if max_delivery_time is not None and max_delivery_time <= int(max_delivery_time_param):
                filtered_queryset.append(offer)
        return filtered_queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        offer = self.get_object()  # Holt die Offer-Instanz basierend auf pk
        serializer = OfferSerializer(offer, context={'request': request})
        user = offer.user  # Verknüpfter User des Angebots

     # Serialisierte Offer-Daten
        offer_data = serializer.data

        # Ergänzte User-Daten
        offer_data["user_details"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
        }

        return Response(offer_data)


class OfferDetailViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet,
                         mixins.DestroyModelMixin):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly &
    #                       IsSuperUser | IsOwnerOrAdmin]
    permission_classes = [IsSuperUser]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderDetailSerializer
        return OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(
            order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def perform_create(self, serializer):
        customer_user = self.request.user
        offer_detail = serializer.validated_data.pop('offer_detail')

        serializer.save(
            customer_user=customer_user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            business_user=offer_detail.user,
            status='in_progress'
        )
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


class ProfilViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedCustom & IsOwnUserOrAdmin]

    def retrieve(self, request, *args, **kwargs):
        # if not request.user.is_authenticated:
        #     return Response(
        #         {"Benutzer ist nicht authentifiziert."},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        try:
            instance = self.get_object()
        except:
            return Response(
                {"message": "Das Benutzerprofil wurde nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')  # Zugriff auf die in der URL angegebene pk
        if not (request.user.id == int(pk)) and not request.user.is_superuser:
            return Response(
                {"Authentifizierter Benutzer ist nicht der Eigentümer des Profils."},
                status=status.HTTP_403_FORBIDDEN
            )
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ProfilTypeViewSet(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedCustom & IsSuperUser]

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
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": username, "email": user.email, "user_id": user.pk}, status=status.HTTP_201_CREATED)
        return Response({"Ungültige Anfragedaten."}, status=status.HTTP_400_BAD_REQUEST)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

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

        return Response(data, status=status.HTTP_201_CREATED)


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
