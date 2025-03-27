from rest_framework import viewsets, generics
from ..models import Offer, OfferDetail, Order, Review, BaseInfo
from .serializers import OfferSerializer, OfferDetailSerializer, OrderSerializer, UserSerializer, CustomUser, CustomerUserSerializer, BusinessUserSerializer, RegistrationSerializer, ReviewSerializer, ReviewDetailSerializer, OrderDetailSerializer, BaseInfoSerializer
from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from .permissions import IsOwnerOrAdmin, IsBusinessUser, IsSuperUser, IsOwnUserOrAdmin, IsAuthenticatedCustom, IsAuthenticatedOrRealOnlyCustom, IsCustomerUser
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Min, Avg
from rest_framework.exceptions import PermissionDenied, ValidationError
from .filters import ReviewFilter


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": username, "email": user.email, "user_id": user.pk}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)


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


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 6
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticatedOrRealOnlyCustom,
                          IsBusinessUser, IsOwnerOrAdmin]
    pagination_class = CustomLimitOffsetPagination
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']  # Erlaubte Felder
    # ordering = ['-min_price']  # Standard-Sortierung (hier: neueste zuerst)

    def get_queryset(self):
        queryset = Offer.objects.annotate(
            min_price=Min('details__price'),
            # Berechnet die kürzeste Lieferzeit
            max_delivery_time=Min('details__delivery_time_in_days')
        )

        # Filter nach Ersteller
        creator_id_param = self.request.query_params.get('creator_id')
        if creator_id_param:
            queryset = queryset.filter(user__id=creator_id_param)

        # Filter nach Mindestpreis
        min_price_param = self.request.query_params.get('min_price')
        if min_price_param:
            queryset = queryset.filter(min_price__lte=float(min_price_param))

        # Filter nach maximaler Lieferzeit
        max_delivery_time_param = self.request.query_params.get(
            'max_delivery_time')
        if max_delivery_time_param:
            queryset = queryset.filter(
                max_delivery_time__lte=int(max_delivery_time_param))

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({
                'details': 'Ungültige Anfragedaten oder unvollständige Details.'
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        if request.user.is_authenticated:
            try:
                offer = self.get_object()  # Holt die Offer-Instanz basierend auf pk
                serializer = OfferSerializer(
                    offer, context={'request': request})
                user = offer.user  # Verknüpfter User des Angebots
            except:
                return Response({'details': 'Das Angebot mit der angegebenen ID wurde nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'details': 'Benutzer ist nicht authentifiziert.'}, status=status.HTTP_401_UNAUTHORIZED)

     # Serialisierte Offer-Daten
        offer_data = serializer.data

        # Ergänzte User-Daten
        offer_data["user_details"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
        }

        return Response(offer_data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        try:
            kwargs['partial'] = True
            return self.update(request, *args, **kwargs)
        except:
            return Response({'details': 'Das Angebot mit der angegebenen ID wurde nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)


class OfferDetailViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet,
                         mixins.DestroyModelMixin):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly &
    #                       IsSuperUser | IsOwnerOrAdmin]
    permission_classes = [IsAuthenticatedCustom & IsSuperUser]

    def retrieve(self, request, pk=None):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except:
            return Response({'details': 'Das Angebot mit der angegebenen ID wurde nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticatedCustom]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderDetailSerializer
        return OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            order = self.get_object()
            print(order)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except:
            return Response(
                {'details': 'Die angegebene Bestellung wurde nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, *args, **kwargs):
        if self.request.user.type != 'business':
            raise PermissionDenied(
                'Nur Business-User dürfen Bestellungen aktualisieren.')

        try:
            order = self.get_object()
            serializer = self.get_serializer(
                order, data=request.data, partial=True)
            erializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except:
            return Response(
                {'details': 'Ungültiger Status oder unzulässige Felder in der Anfrage'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        if self.request.user.type != 'customer':
            raise PermissionDenied(
                'Nur Customer-User dürfen Bestellungen erstellen.')

        customer_user = self.request.user
        offer_detail = serializer.validated_data.pop('offer_detail', None)

        if offer_detail is None:
            raise ValidationError(
                {'details': 'Kein gültiges OfferDetail angegeben.'})

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

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'details': 'Benutzer hat keine Berechtigung, die Bestellung zu löschen.'}, status=status.HTTP_403_FORBIDDEN)


class OrderCountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedCustom]

    def retrieve(self, request, pk=None):
        try:
            business_user = CustomUser.objects.filter(pk=pk).first()

            if business_user.type != 'business':
                return Response({"error": "Kein Geschäftsnutzer mit der angegebenen ID gefunden"}, status=status.HTTP_404_NOT_FOUND)

            order_count = Order.objects.filter(
                business_user=business_user, status='in_progress'
            ).count()
            return Response({"order_count": order_count})
        except:
            return Response({"error": "Kein Geschäftsnutzer mit der angegebenen ID gefunden"}, status=status.HTTP_404_NOT_FOUND)


class CompletedOrderCountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedCustom]

    def retrieve(self, request, pk=None):
        try:
            business_user = CustomUser.objects.filter(pk=pk).first()

            if business_user.type != 'business':
                return Response({"error": "Kein Geschäftsnutzer mit der angegebenen ID gefunden"}, status=status.HTTP_404_NOT_FOUND)

            order_count = Order.objects.filter(
                business_user=business_user, status='completed'
            ).count()
            return Response({"order_count": order_count})
        except:
            return Response({"error": "Kein Geschäftsnutzer mit der angegebenen ID gefunden"}, status=status.HTTP_404_NOT_FOUND)


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


class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticatedCustom, IsCustomerUser]
    filterset_class = ReviewFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewSerializer
        elif self.action == 'update':
            return ReviewDetailSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        business_user = validated_data.get("business_user")
        reviewer = self.request.user

        if Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
            raise PermissionDenied(
                "Forbidden. Ein Benutzer kann nur eine Bewertung pro Geschäftsprofil abgeben.")

        serializer.save(reviewer=reviewer)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if instance.reviewer != self.request.user:
            raise PermissionDenied(
                "Forbidden. Der Benutzer ist nicht berechtigt, diese Bewertung zu bearbeiten.")

        serializer.save(reviewer=self.request.user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.reviewer != self.request.user:
            raise PermissionDenied(
                "Forbidden. Der Benutzer ist nicht berechtigt, diese Bewertung zu löschen.")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseInfoView(viewsets.ViewSet):

    def list(self, request, pk=None):
        review_count = Review.objects.all().count() or 0
        average_rating = Review.objects.aggregate(Avg('rating')) or 0
        business_profile_count = CustomUser.objects.filter(
            type='business').count() or 0
        offer_count = Offer.objects.all().count() or 0

        return Response({
            "review_count": review_count,
            "average_rating": average_rating['rating__avg'],
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        }, status=status.HTTP_200_OK)
