"""
API views for the tow truck backend rewritten to match the updated data model.
"""

from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    ClientVehicle,
    Notification,
    NotificationType,
    Order,
    OrderStatusHistory,
    Payment,
    Rating,
    SupportMessage,
    SupportTicket,
    TicketStatus,
    TowTruck,
    User,
    VehicleType,
)
from .serializers import (
    LocationUpdateSerializer,
    NotificationSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
    PasswordResetSerializer,
    PaymentSerializer,
    PriceEstimateRequestSerializer,
    PriceEstimateResponseSerializer,
    RatingSerializer,
    SupportMessageCreateSerializer,
    SupportMessageSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
    SupportTicketUpdateSerializer,
    TowTruckSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    VehicleTypeSerializer,
    WeatherRequestSerializer,
    WeatherResponseSerializer,
)
from .services.pricing import calculate_price, fetch_weather, simplify_weather


# ---------------------------------------------------------------------------
# Authentication and profile
# ---------------------------------------------------------------------------


class UserRegistrationView(generics.CreateAPIView):
    """Allow clients or drivers to register and immediately receive JWT tokens."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate a user by phone and password and issue JWT tokens."""

    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    """Reset the password using a phone number."""

    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Пароль успешно обновлён."})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the current user's profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


class VehicleTypeListView(generics.ListAPIView):
    """List available tow truck categories."""

    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]
    queryset = VehicleType.objects.all().order_by("name")


class VehicleTypeDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a single vehicle type (operators only for writes)."""

    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]
    queryset = VehicleType.objects.all()

    def perform_update(self, serializer):
        user = self.request.user
        if not (getattr(user, "is_staff", False) or getattr(user, "user_type_id", None) == "OPERATOR"):
            raise PermissionDenied("Только операторы могут изменять тарифы.")
        serializer.save()


class TowTruckListView(generics.ListAPIView):
    """List tow trucks that are currently available."""

    serializer_class = TowTruckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = TowTruck.objects.select_related("driver").filter(status="AVAILABLE")
        vehicle_type_id = self.request.query_params.get("vehicle_type")
        if vehicle_type_id:
            queryset = queryset.filter(vehicle_types__id=vehicle_type_id)
        return queryset


# ---------------------------------------------------------------------------
# Orders and logistics
# ---------------------------------------------------------------------------


class OrderCreateView(generics.CreateAPIView):
    """Create an order on behalf of the authenticated client."""

    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save()

        notification_code = "ORDER_CREATED"
        if NotificationType.objects.filter(code=notification_code).exists():
            Notification.objects.create(
                user=self.request.user,
                notification_type_id=notification_code,
                title="Заказ создан",
                message=f"Заказ {order.id} успешно отправлен в обработку.",
                related_order=order,
            )


class OrderListView(generics.ListAPIView):
    """List orders for the current user depending on their role."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not user.is_authenticated:
            return Order.objects.none()

        base = Order.objects.select_related(
            "client",
            "vehicle",
            "vehicle_type",
            "tow_truck",
            "tow_truck__driver",
        )
        user_type = getattr(user, "user_type_id", None)
        if user_type == "CLIENT":
            return base.filter(client=user)
        if user_type == "DRIVER":
            return base.filter(tow_truck__driver=user)
        if user_type == "OPERATOR" or user.is_staff:
            return base
        return Order.objects.none()


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or partially update an order the user has access to."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not user.is_authenticated:
            return Order.objects.none()

        base = Order.objects.select_related(
            "client",
            "vehicle",
            "vehicle_type",
            "tow_truck",
            "tow_truck__driver",
        )
        user_type = getattr(user, "user_type_id", None)
        if user_type == "CLIENT":
            return base.filter(client=user)
        if user_type == "DRIVER":
            return base.filter(tow_truck__driver=user)
        if user_type == "OPERATOR" or user.is_staff:
            return base
        return Order.objects.none()


class OrderUpdateStatusView(generics.UpdateAPIView):
    """Allow drivers and operators to change order status."""

    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not user.is_authenticated:
            return Order.objects.none()

        user_type = getattr(user, "user_type_id", None)
        if user_type == "DRIVER":
            return Order.objects.filter(tow_truck__driver=user)
        if user_type == "OPERATOR" or user.is_staff:
            return Order.objects.all()
        return Order.objects.none()

    def perform_update(self, serializer):
        order = self.get_object()
        old_status = order.status
        serializer.save()

        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=order.status,
            changed_by=self.request.user,
        )
        self._create_status_notification(order)

    def _create_status_notification(self, order: Order):
        messages = {
            "CONFIRMED": {
                "title": "Заказ подтверждён",
                "message": f"Заказ {order.id} подтверждён оператором.",
            },
            "ASSIGNED": {
                "title": "Назначен эвакуатор",
                "message": f"К заказу {order.id} назначен водитель.",
            },
            "IN_PROGRESS": {
                "title": "Заказ в работе",
                "message": f"Эвакуатор выехал на заказ {order.id}.",
            },
            "COMPLETED": {
                "title": "Заказ выполнен",
                "message": f"Заказ {order.id} успешно завершён.",
            },
            "CANCELLED": {
                "title": "Заказ отменён",
                "message": f"Заказ {order.id} был отменён.",
            },
        }

        payload = messages.get(order.status)
        if not payload:
            return

        code = f"ORDER_{order.status}"
        if not NotificationType.objects.filter(code=code).exists():
            return

        Notification.objects.create(
            user=order.client,
            notification_type_id=code,
            title=payload["title"],
            message=payload["message"],
            related_order=order,
        )


class PriceEstimateView(generics.GenericAPIView):
    """Compute tow truck price for the given vehicle type and coordinates."""

    permission_classes = [IsAuthenticated]
    serializer_class = PriceEstimateRequestSerializer

    def post(self, request, *args, **kwargs):
        request_serializer = self.get_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        vehicle_type: VehicleType = request_serializer.validated_data["vehicle_type"]
        distance_km = request_serializer.validated_data["distance_km"]
        latitude = request_serializer.validated_data["latitude"]
        longitude = request_serializer.validated_data["longitude"]

        total_price, breakdown = calculate_price(
            vehicle_type=vehicle_type,
            distance_km=distance_km,
            lat=latitude,
            lon=longitude,
        )

        response_serializer = PriceEstimateResponseSerializer(
            data={
                "price": total_price,
                "currency": getattr(settings, "DEFAULT_CURRENCY", "RUB"),
                "breakdown": breakdown,
            }
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data)


class WeatherLookupView(generics.GenericAPIView):
    """Return a simple weather report for given coordinates."""

    serializer_class = WeatherRequestSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        weather_payload = fetch_weather(latitude, longitude)
        simplified = simplify_weather(weather_payload)
        response_serializer = WeatherResponseSerializer(simplified or {})
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_location(request):
    """Update driver coordinates and broadcast them to WebSocket subscribers."""

    if getattr(request.user, "user_type_id", None) != "DRIVER":
        return Response({"error": "Обновлять координаты могут только водители."}, status=status.HTTP_403_FORBIDDEN)

    serializer = LocationUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        tow_truck = TowTruck.objects.select_related("driver").get(driver=request.user)
    except TowTruck.DoesNotExist:
        return Response({"error": "За водителем не закреплён эвакуатор."}, status=status.HTTP_404_NOT_FOUND)

    tow_truck.current_location_lat = serializer.validated_data["latitude"]
    tow_truck.current_location_lon = serializer.validated_data["longitude"]
    tow_truck.last_location_update = timezone.now()
    tow_truck.save(update_fields=["current_location_lat", "current_location_lon", "last_location_update"])

    payload = {
        "type": "update",
        "location": {
            "tow_truck_id": str(tow_truck.id),
            "latitude": tow_truck.current_location_lat,
            "longitude": tow_truck.current_location_lon,
            "updated_at": tow_truck.last_location_update.isoformat(),
        },
    }

    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"tow_truck_{tow_truck.id}",
            {"type": "location_update", "payload": payload | {"tow_truck_id": str(tow_truck.id)}},
        )

        active_statuses = ["PENDING", "CONFIRMED", "ASSIGNED", "IN_PROGRESS"]
        for order_id in Order.objects.filter(tow_truck=tow_truck, status__in=active_statuses).values_list("id", flat=True):
            async_to_sync(channel_layer.group_send)(
                f"order_{order_id}",
                {"type": "location_update", "payload": payload | {"order_id": str(order_id)}},
            )

    return Response({"message": "Координаты обновлены.", "location": payload["location"]})


# ---------------------------------------------------------------------------
# Support tickets
# ---------------------------------------------------------------------------


class SupportTicketListCreateView(generics.ListCreateAPIView):
    """List current user's tickets or create a new ticket."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SupportTicket.objects.none()

        queryset = SupportTicket.objects.select_related(
            "author",
            "assigned_to",
            "related_order",
            "status",
        )
        user = self.request.user
        if not user.is_authenticated:
            return SupportTicket.objects.none()
        if user.is_staff or getattr(user, "user_type_id", None) == "OPERATOR":
            return queryset.order_by("-created_at")
        return queryset.filter(author=user).order_by("-created_at")

    def get_serializer_class(self):
        return SupportTicketCreateSerializer if self.request.method == "POST" else SupportTicketSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        status_obj = TicketStatus.objects.filter(code="OPEN").first()
        if status_obj is None:
            status_obj = TicketStatus.objects.first()
        ticket = serializer.save(author=self.request.user, status=status_obj)
        message = SupportMessage.objects.create(
            ticket=ticket,
            author=self.request.user,
            body=ticket.description,
            is_internal=False,
        )
        ticket.last_message_at = message.created_at
        ticket.save(update_fields=["last_message_at"])


class SupportTicketDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a ticket. Updates are limited to operators."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SupportTicket.objects.none()
        queryset = SupportTicket.objects.select_related(
            "author",
            "assigned_to",
            "related_order",
            "status",
        ).prefetch_related("messages__author")
        user = self.request.user
        if not user.is_authenticated:
            return SupportTicket.objects.none()
        if user.is_staff or getattr(user, "user_type_id", None) == "OPERATOR":
            return queryset
        return queryset.filter(author=user)

    def get_serializer_class(self):
        return SupportTicketUpdateSerializer if self.request.method in ("PUT", "PATCH") else SupportTicketSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_update(self, serializer):
        user = self.request.user
        if not (user.is_staff or getattr(user, "user_type_id", None) == "OPERATOR"):
            disallowed = set(serializer.validated_data.keys()) - {"priority"}
            if disallowed:
                raise PermissionDenied("Только операторы могут менять статус или исполнителя.")
        serializer.save()


class SupportMessageListCreateView(generics.ListCreateAPIView):
    """List or create messages for a specific ticket."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return SupportMessageCreateSerializer if self.request.method == "POST" else SupportMessageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_ticket(self) -> SupportTicket:
        if not hasattr(self, "_ticket"):
            ticket = get_object_or_404(
                SupportTicket.objects.select_related("author", "assigned_to", "status"),
                id=self.kwargs["ticket_id"],
            )
            if not self._has_access(ticket):
                raise PermissionDenied("Нет доступа к тикету.")
            self._ticket = ticket
        return self._ticket

    def _has_access(self, ticket: SupportTicket) -> bool:
        user = self.request.user
        if user.is_staff or getattr(user, "user_type_id", None) == "OPERATOR":
            return True
        if user.is_authenticated and ticket.author_id == user.id:
            return True
        if user.is_authenticated and ticket.assigned_to_id == user.id:
            return True
        return False

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SupportMessage.objects.none()
        ticket = self.get_ticket()
        return ticket.messages.select_related("author").order_by("created_at")

    def perform_create(self, serializer):
        ticket = self.get_ticket()
        message = serializer.save(ticket=ticket, author=self.request.user)

        updates: dict[str, object] = {"last_message_at": message.created_at}
        if ticket.status_id == "OPEN" and self.request.user != ticket.author:
            in_progress = TicketStatus.objects.filter(code="IN_PROGRESS").first()
            if in_progress:
                updates["status"] = in_progress
        if ticket.assigned_to is None and (self.request.user.is_staff or getattr(self.request.user, "user_type_id", None) == "OPERATOR"):
            updates["assigned_to"] = self.request.user

        if updates:
            for field, value in updates.items():
                setattr(ticket, field, value)
            ticket.save(update_fields=list(updates.keys()))


# ---------------------------------------------------------------------------
# Payments, ratings and notifications
# ---------------------------------------------------------------------------


class PaymentCreateView(generics.CreateAPIView):
    """Create a payment for an order belonging to the current client."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = get_object_or_404(Order, id=self.kwargs.get("order_id"), client=self.request.user)
        serializer.save(order=order)


class RatingCreateView(generics.CreateAPIView):
    """Submit a rating for a completed order."""

    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = get_object_or_404(
            Order,
            id=self.kwargs.get("order_id"),
            client=self.request.user,
            status="COMPLETED",
        )
        serializer.save(order=order)


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.select_related("notification_type", "related_order").filter(
            user=self.request.user
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id: int):
    """Mark a notification as read."""

    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return Response({"message": "Уведомление отмечено как прочитанное."})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Aggregate high-level statistics for dashboards depending on role."""

    user = request.user
    if not user.is_authenticated:
        return Response({})

    stats: dict[str, object]
    user_type = getattr(user, "user_type_id", None)

    if user_type == "CLIENT":
        stats = {
            "total_orders": Order.objects.filter(client=user).count(),
            "active_orders": Order.objects.filter(
                client=user,
                status__in=["PENDING", "CONFIRMED", "ASSIGNED", "IN_PROGRESS"],
            ).count(),
            "completed_orders": Order.objects.filter(client=user, status="COMPLETED").count(),
            "unread_notifications": Notification.objects.filter(user=user, is_read=False).count(),
        }
    elif user_type == "DRIVER":
        driver_orders = Order.objects.filter(tow_truck__driver=user)
        avg_rating = (
            driver_orders.filter(rating__isnull=False).aggregate(avg=models.Avg("rating__driver_rating"))["avg"] or 0
        )
        stats = {
            "total_orders": driver_orders.count(),
            "active_orders": driver_orders.filter(status__in=["ASSIGNED", "IN_PROGRESS"]).count(),
            "completed_orders": driver_orders.filter(status="COMPLETED").count(),
            "avg_rating": avg_rating,
            "unread_notifications": Notification.objects.filter(user=user, is_read=False).count(),
        }
    elif user_type == "OPERATOR" or user.is_staff:
        stats = {
            "total_orders": Order.objects.count(),
            "pending_orders": Order.objects.filter(status="PENDING").count(),
            "active_orders": Order.objects.filter(
                status__in=["CONFIRMED", "ASSIGNED", "IN_PROGRESS"]
            ).count(),
            "available_trucks": TowTruck.objects.filter(status="AVAILABLE").count(),
            "unread_notifications": Notification.objects.filter(user=user, is_read=False).count(),
        }
    else:
        stats = {}

    return Response(stats)
