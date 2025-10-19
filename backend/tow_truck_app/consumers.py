from typing import Optional
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken

from .models import Order, TowTruck

User = get_user_model()


class LocationConsumer(AsyncJsonWebsocketConsumer):
    """
    Stream real-time tow truck coordinates to subscribed WebSocket clients.

    Clients can subscribe either to a specific order group (``order_<uuid>``) or to a tow
    truck group (``tow_truck_<uuid>``). Authentication occurs through the Django session
    or a JWT access token passed via the query string.
    """

    group_name: Optional[str] = None
    order: Optional[Order] = None
    tow_truck: Optional[TowTruck] = None
    user: Optional[User] = None

    async def connect(self) -> None:
        self.user = await self._authenticate()
        if not self.user:
            await self.close(code=4001)
            return

        route_kwargs = self.scope.get("url_route", {}).get("kwargs", {})
        order_id = route_kwargs.get("order_id")
        tow_truck_id = route_kwargs.get("tow_truck_id")

        if order_id:
            self.order = await self._get_order(order_id)
            if not self.order:
                await self.close(code=4004)
                return
            if not await self._can_access_order(self.order):
                await self.close(code=4003)
                return
            self.group_name = f"order_{self.order.id}"
        elif tow_truck_id:
            self.tow_truck = await self._get_tow_truck(tow_truck_id)
            if not self.tow_truck:
                await self.close(code=4004)
                return
            if not await self._can_access_tow_truck(self.tow_truck):
                await self.close(code=4003)
                return
            self.group_name = f"tow_truck_{self.tow_truck.id}"
        else:
            await self.close(code=4000)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send the most recent coordinate snapshot, if it is already known.
        initial_payload = await self._build_payload()
        if initial_payload:
            await self.send_json(initial_payload)

    async def disconnect(self, close_code: int) -> None:
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data: str | bytes | None = None, bytes_data: bytes | None = None) -> None:
        """Inbound client messages are ignored: this channel is broadcast-only."""
        return

    async def location_update(self, event: dict) -> None:
        """Forward broadcast events to the connected client."""
        await self.send_json(event.get("payload", {}))

    async def _authenticate(self) -> Optional[User]:
        """
        Resolve the current user either from the session (preferred) or via a JWT access token.
        """
        scope_user = self.scope.get("user")
        if scope_user and scope_user.is_authenticated:
            return scope_user

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token") or params.get("access") or params.get("access_token")
        if not token_list:
            return None

        try:
            token = AccessToken(token_list[0])
        except InvalidToken:
            return None

        user_id = token.get("user_id")
        if not user_id:
            return None

        return await self._get_user(user_id)

    @database_sync_to_async
    def _get_user(self, user_id: int) -> Optional[User]:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_order(self, order_id) -> Optional[Order]:
        try:
            return Order.objects.select_related("client", "tow_truck", "tow_truck__driver").get(id=order_id)
        except Order.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_tow_truck(self, tow_truck_id) -> Optional[TowTruck]:
        try:
            return TowTruck.objects.select_related("driver").get(id=tow_truck_id)
        except TowTruck.DoesNotExist:
            return None

    @database_sync_to_async
    def _can_access_order(self, order: Order) -> bool:
        if not self.user:
            return False
        if self.user.is_staff or getattr(self.user, "user_type", None) == "OPERATOR":
            return True
        if order.client_id == self.user.id:
            return True
        if order.tow_truck and order.tow_truck.driver_id == self.user.id:
            return True
        return False

    @database_sync_to_async
    def _can_access_tow_truck(self, tow_truck: TowTruck) -> bool:
        if not self.user:
            return False
        if self.user.is_staff or getattr(self.user, "user_type", None) == "OPERATOR":
            return True
        if tow_truck.driver_id == self.user.id:
            return True
        return False

    @database_sync_to_async
    def _current_location(self) -> Optional[dict]:
        tow_truck = self.tow_truck
        if not tow_truck and self.order:
            tow_truck = self.order.tow_truck
        if not tow_truck:
            return None
        if tow_truck.current_location_lat is None or tow_truck.current_location_lon is None:
            return None
        return {
            "tow_truck_id": str(tow_truck.id),
            "latitude": tow_truck.current_location_lat,
            "longitude": tow_truck.current_location_lon,
            "updated_at": tow_truck.last_location_update.isoformat() if tow_truck.last_location_update else None,
        }

    async def _build_payload(self) -> Optional[dict]:
        location = await self._current_location()
        if not location:
            return None

        payload: dict[str, object] = {
            "type": "initial",
            "location": location,
        }

        if self.order:
            payload["order_id"] = str(self.order.id)
        if self.tow_truck:
            payload["tow_truck_id"] = str(self.tow_truck.id)

        return payload
