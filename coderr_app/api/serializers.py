from rest_framework import serializers
from ..models import Offer, OfferDetail, Order, CustomUser


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

    def create(self, validated_data):
        # Setze den logged-in User als 'customer_user'
        validated_data['customer_user'] = self.context['request'].user

        # Hole die OfferDetail-Instanz aus 'validated_data'
        offer_detail = validated_data.pop('offer_detail')

        # Erstelle die Order mit den OfferDetail-Daten
        order = Order.objects.create(
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            business_user=offer_detail.owner,
            ** validated_data
        )
        if order.status is None:
            order.status = 'in_progress'
            order.save()

        return order


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
        # fields = '__all__'

    def get_user(self, obj):
        return {
            'pk': obj.pk,
            'username': obj.username,
            'first_name': obj.first_name,
            'last_name': obj.last_name
        }
