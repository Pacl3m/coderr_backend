from rest_framework import serializers
from ..models import Offer, OfferDetail, Order, CustomUser, Review, BaseInfo


class OfferDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfferDetail
        exclude = ['offer', 'user']

    def validate(self, data):
        required_fields = ['title', 'revisions',
                           'delivery_time_in_days', 'price', 'features', 'offer_type']

        missing_fields = [
            field for field in required_fields if field not in data]

        if missing_fields:
            raise serializers.ValidationError(
                {field: f"{field} ist erforderlich." for field in missing_fields}
            )

        return data


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='offerdetails-detail')

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class OfferSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image',
                  'description', 'details', 'created_at', 'updated_at', 'user_details', 'min_price', 'min_delivery_time']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def get_fields(self):
        fields = super().get_fields()

        if self.context['request'].method in ['POST', 'PATCH', 'PUT']:
            fields['details'] = OfferDetailSerializer(many=True)
        else:
            fields['details'] = OfferDetailLinkSerializer(many=True)

        return fields

    def get_min_price(self, obj):
        offer_details = obj.details.all()
        return min(detail.price for detail in offer_details)

    def get_min_delivery_time(self, obj):
        offer_details = obj.details.all()
        return min(detail.delivery_time_in_days for detail in offer_details)

    def get_user_details(self, obj):
        user = obj.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].method == 'POST':
            representation.pop('user_details', None)
            representation.pop('min_price', None)
            representation.pop('min_delivery_time', None)
        return representation

    def validate_details(self, value):
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

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
                user=self.context['request'].user,
                defaults=detail_data
            )


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'title', 'revisions',
                            'delivery_time_in_days', 'price', 'features', 'offer_type', 'created_at',
                            'updated_at', 'customer_user', 'business_user']


class OrderDetailSerializer(serializers.ModelSerializer):
    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.all(),
        source='offer_detail',
        write_only=True
    )

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'title', 'revisions',
                            'delivery_time_in_days', 'price', 'features', 'offer_type', 'status', 'created_at',
                            'updated_at', 'customer_user', 'business_user']


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
                {'details': 'Ungültige Anfragedaten.'})

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'details': 'Diese E-Mail-Adresse wird bereits verwendet.'})

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {'details': 'Dieser Benutzername ist bereits vergeben.'})

        account = CustomUser(
            email=self.validated_data['email'], username=self.validated_data['username'], type=self.validated_data['type'])
        account.set_password(pw)
        account.save()
        return account


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating',
                  'description', 'created_at', 'updated_at']
        extra_kwargs = {
            'reviewer': {'read_only': True}
        }


class ReviewDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ['rating', 'description']
