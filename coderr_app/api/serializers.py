from rest_framework import serializers
from ..models import Offer, OfferDetail, Order, CustomUser, Review


class OfferDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfferDetail
        exclude = ['offer', 'owner']


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'details']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        validated_data['user'] = self.context['request'].user
        offer = super().create(validated_data)

        self._create_or_update_offer_details(offer, details_data)
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        instance = super().update(instance, validated_data)

        if details_data:
            self._create_or_update_offer_details(instance, details_data)

        return instance

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def _create_or_update_offer_details(self, offer, details_data):
        for detail_data in details_data:
            offer_type = detail_data.get('offer_type')
            detail_instance, created = OfferDetail.objects.update_or_create(
                offer=offer,
                offer_type=offer_type,
                owner=self.context['request'].user,
                defaults=detail_data
            )


class OrderSerializer(serializers.ModelSerializer):
    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.all(),  # Validierung der ID
        source='offer_detail',  # Verknüpfung mit dem Feld im Modell
        write_only=True  # Nur beim POST sichtbar
    )

    class Meta:
        model = Order
        fields = '__all__'

    # def create(self, validated_data):
    #     # Setze den logged-in User als 'customer_user'
    #     validated_data['customer_user'] = self.context['request'].user

    #     # Hole die OfferDetail-Instanz aus 'validated_data'
    #     offer_detail = validated_data.pop('offer_detail')

    #     # Erstelle die Order mit den OfferDetail-Daten
    #     order = Order.objects.create(
    #         title=offer_detail.title,
    #         revisions=offer_detail.revisions,
    #         delivery_time_in_days=offer_detail.delivery_time_in_days,
    #         price=offer_detail.price,
    #         features=offer_detail.features,
    #         offer_type=offer_detail.offer_type,
    #         business_user=offer_detail.owner,
    #         ** validated_data
    #     )
    #     if order.status is None:
    #         order.status = 'in_progress'
    #         order.save()

    #     return order


class UserSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='id')

    class Meta:
        model = CustomUser
        fields = ["user", "username", "first_name",
                  "last_name", "file", "location", "tel", "description", "working_hours", "type",
                  "email", "created_at"]


class BusinessUserSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['user', 'file', 'location', 'tel',
                  'description', 'working_hours', 'type']

    def get_user(self, obj):
        return {
            'pk': obj.pk,
            'username': obj.username,
            'first_name': obj.first_name,
            'last_name': obj.last_name
        }


class CustomerUserSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['user', 'file', 'type', 'created_at']

    def get_user(self, obj):
        return {
            'pk': obj.pk,
            'username': obj.username,
            'first_name': obj.first_name,
            'last_name': obj.last_name
        }


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        error_messages={
            'invalid': ["E-Mail ist erforderlich.", "E-Mail-Format ist ungültig."]
        }
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def save(self, **kwargs):
        username = self.validated_data['username']
        pw = self.validated_data['password']
        repeated_pw = self.validated_data['repeated_password']
        email = self.validated_data['email']

        if pw != repeated_pw:
            raise serializers.ValidationError(
                {'error': 'Passwords dont match'})

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'email': ['Diese E-Mail-Adresse wird bereits verwendet.']})

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {'username': ['Dieser Benutzername ist bereits vergeben.']})

        account = CustomUser(
            email=self.validated_data['email'], username=self.validated_data['username'], type=self.validated_data['type'])
        account.set_password(pw)
        account.save()
        return account


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = '__all__'
        extra_kwargs = {
            'reviewer': {'read_only': True}
        }


class ReviewDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ['rating', 'description']
