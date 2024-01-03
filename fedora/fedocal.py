import requests
from itertools import tee, chain, islice
from operator import itemgetter
from maubot.handlers import command
from maubot import MessageEvent
from .clients.fedocal import FedocalClient
from .handler import Handler

class FedocalHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.fedocal_client = FedocalClient()

    @command.new(name="nextmeeting", help="Get the next meeting in a room")
    @command.argument("room", required=True)
    async def next_meeting(self, evt: MessageEvent, room: str) -> None:
        await evt.mark_read()
        meetings = await self.fedocal_client.get_next_meetings(room)
        if not meetings:
            await evt.respond(f"No meetings scheduled for #{room}.")
            return
        await evt.respond(f"Next Meeting in #{room}:")
        for date, meeting in islice(meetings, 0, 1):
            response = f"{meeting['meeting_name']} (starting {date.humanize()})"
            await evt.respond(response)


    @command.new(name="nextmeetings", help="Get the next 3 meetings in a room")
    @command.argument("room", required=True)
    async def next_meetings(self, evt: MessageEvent, room: str) -> None:
        await evt.mark_read()
        meetings = await self.fedocal_client.get_next_meetings(room)
        if not meetings:
            await evt.respond(f"No meetings scheduled for #{room}.")
            return
        await evt.respond(f"Next Meetings in #{room}:")
        for date, meeting in islice(meetings, 0, 3):
            response = f"- {meeting['meeting_name']} (starting {date.humanize()})"
            await evt.respond(response)

