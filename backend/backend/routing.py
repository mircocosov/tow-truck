from django.urls import path

from tow_truck_app import consumers

websocket_urlpatterns = [
    path(
        "ws/orders/<uuid:order_id>/location/",
        consumers.LocationConsumer.as_asgi(),
        name="ws-order-location",
    ),
    path(
        "ws/tow-trucks/<uuid:tow_truck_id>/location/",
        consumers.LocationConsumer.as_asgi(),
        name="ws-tow-truck-location",
    ),
]
