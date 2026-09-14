from __future__ import annotations
import asyncio
import json
from typing import Any, Protocol

from .config import SMS_API_KEY, SMS_PROVIDER, SMS_SENDER_ID, SMTP_HOST, SMTP_USER, EMAIL_FROM


class AlertStream:
    """Fan-out bus for connected browser clients (SSE subscribers)."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        async with self._lock:
            self._subscribers.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def connected_clients(self) -> int:
        return len(self._subscribers)

    async def publish(self, event: dict[str, Any]) -> None:
        payload = f"event: alert\ndata: {json.dumps(event, default=str)}\n\n"
        async with self._lock:
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # Drop oldest queued message to keep the feed flowing.
                try:
                    q.get_nowait()
                    q.put_nowait(payload)
                except Exception:  # noqa: BLE001
                    pass


stream = AlertStream()


class NotificationProvider(Protocol):
    id: str
    label: str

    def available(self) -> bool: ...

    async def deliver(self, alert: dict[str, Any]) -> dict[str, Any]: ...


class LocalRealtimeProvider:
    id = "local_realtime"
    label = "Connected browser clients (SSE/WebSocket)"

    def available(self) -> bool:
        return True

    async def deliver(self, alert: dict[str, Any]) -> dict[str, Any]:
        count = stream.connected_clients()
        if count > 0:
            await stream.publish(alert)
        return {"channel": self.id, "status": "DELIVERED" if count else "NO_CLIENTS", "clients": count}


class SmsProvider:
    id = "sms"
    label = "SMS (provider configured)"

    def available(self) -> bool:
        return bool(SMS_PROVIDER and SMS_API_KEY)

    async def deliver(self, alert: dict[str, Any]) -> dict[str, Any]:
        # Real adapters (Twilio/TextLocal) plug in here. Never fakes delivery.
        return {"channel": self.id, "status": "NOT_CONFIGURED" if not self.available() else "REQUIRES_ADAPTER", "recipients": 0}


class EmailProvider:
    id = "email"
    label = "Email"

    def available(self) -> bool:
        return bool(SMTP_HOST and SMTP_USER and EMAIL_FROM)

    async def deliver(self, alert: dict[str, Any]) -> dict[str, Any]:
        return {"channel": self.id, "status": "NOT_CONFIGURED" if not self.available() else "REQUIRES_ADAPTER", "recipients": 0}


class DemoProvider:
    id = "demo"
    label = "Demo delivery log"

    def available(self) -> bool:
        return True

    async def deliver(self, alert: dict[str, Any]) -> dict[str, Any]:
        return {"channel": self.id, "status": "DEMO_LOG", "recipients": 0}


PROVIDERS: list[NotificationProvider] = [
    LocalRealtimeProvider(),
    SmsProvider(),
    EmailProvider(),
    DemoProvider(),
]


async def deliver_alert(alert: dict[str, Any], requested_channels: list[str]) -> dict[str, Any]:
    """Deliver an alert across requested (or default) channels.

    local_realtime is always attempted. SMS/email are marked NOT_CONFIGURED
    unless real credentials exist — we never report a non-existent delivery.
    """
    requested = set(requested_channels) if requested_channels else {"local_realtime"}
    results: dict[str, Any] = {}
    for provider in PROVIDERS:
        if provider.id == "local_realtime" or provider.id in requested:
            res = await provider.deliver(alert)
            results[provider.id] = res
    return results