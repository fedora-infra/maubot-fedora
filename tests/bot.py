import asyncio
import time
from dataclasses import dataclass
from unittest import mock

from maubot.matrix import MaubotMatrixClient, MaubotMessageEvent
from mautrix.api import HTTPAPI
from mautrix.types import (
    EventContent,
    EventType,
    MessageEvent,
    MessageType,
    RoomID,
    TextMessageEventContent,
)


@dataclass
class SentEvent:
    room_id: RoomID
    event_type: EventType
    content: EventContent
    kwargs: dict


class TestBot(MaubotMatrixClient):
    def __init__(self):
        api = HTTPAPI(base_url="http://matrix.example.com")
        self.client = MaubotMatrixClient(api=api)
        self.sent = []
        self.client.send_message_event = self._mock_send_message_event
        self.client.send_receipt = mock.AsyncMock()
        self.client.mxid = "@botname:example.com"

    async def _mock_send_message_event(self, room_id, event_type, content, txn_id=None, **kwargs):
        self.sent.append(
            SentEvent(room_id=room_id, event_type=event_type, content=content, kwargs=kwargs)
        )

    async def dispatch(self, event_type: EventType, event):
        tasks = self.client.dispatch_manual_event(event_type, event, force_synchronous=True)
        return await asyncio.gather(*tasks)

    async def send(
        self,
        content,
        html=None,
        room_id="testroom",
        msg_type=MessageType.TEXT,
        sender="@dummy:example.com",
    ):
        event = make_message(content, html=html, room_id=room_id, msg_type=msg_type, sender=sender)
        await self.dispatch(EventType.ROOM_MESSAGE, MaubotMessageEvent(event, self.client))


def make_message(
    content, html=None, room_id="testroom", msg_type=MessageType.TEXT, sender="@dummy:example.com"
):
    return MessageEvent(
        type=EventType.ROOM_MESSAGE,
        room_id=room_id,
        event_id="test",
        sender=sender,
        timestamp=int(time.time()),
        content=TextMessageEventContent(msgtype=msg_type, body=content, formatted_body=html),
    )
