from django.urls import re_path
from .consumers import LiveMatchConsumer, BiroMatchAdminConsumer

websocket_urlpatterns = [
    re_path(r'ws/match/(?P<match_id>\d+)/$', LiveMatchConsumer.as_asgi()),
    re_path(r'ws/biro/match/(?P<match_id>\d+)/$', BiroMatchAdminConsumer.as_asgi()),
]

print(f"[WebSocket Routing] Loaded {len(websocket_urlpatterns)} WebSocket URL patterns:")
for pattern in websocket_urlpatterns:
    print(f"  - {pattern.pattern}")
