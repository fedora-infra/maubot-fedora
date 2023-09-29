import asyncio
from dataclasses import dataclass

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

    async def _mock_send_message_event(self, room_id, event_type, content, txn_id=None, **kwargs):
        self.sent.append(
            SentEvent(room_id=room_id, event_type=event_type, content=content, kwargs=kwargs)
        )

    async def send(self, content, room_id="testroom"):
        event = make_message(content, room_id)
        tasks = self.client.dispatch_manual_event(
            EventType.ROOM_MESSAGE, MaubotMessageEvent(event, self.client), force_synchronous=True
        )
        return await asyncio.gather(*tasks)


def make_message(content, room_id="testroom"):
    return MessageEvent(
        type=EventType.ROOM_MESSAGE,
        room_id=room_id,
        event_id="test",
        sender="@dummy:example.com",
        timestamp=0,
        content=TextMessageEventContent(msgtype=MessageType.TEXT, body=content),
    )
