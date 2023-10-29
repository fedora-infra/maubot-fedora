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
        for date, meeting in islice(meetings, 0, 3):
            response = f"In #{room}@fedoraproject.org is {meeting['meeting_name']} (starting {date.humanize()})"
            await evt.respond(response)

    @command.new(name="nextmeetings", help="Get the next meetings in all rooms")
    async def next_meetings(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        rooms = await self.fedocal_client.get_matrix_rooms()
        if not rooms:
            await evt.respond("No Matrix (@fedoraproject.org) rooms found in Fedocal.")
            return

        meetings_by_room = {}
        for room in rooms:
            meetings = await self.fedocal_client.get_next_meetings(room)
            if meetings:
                meetings_by_room[room] = meetings

        if not meetings_by_room:
            await evt.respond("No meetings scheduled in any room.")
            return

        for room, meetings in meetings_by_room.items():
            await evt.respond(f"Meetings in #{room}:")
            for date, meeting in islice(meetings, 0, 3):
                response = f"- {meeting['meeting_name']} (starting {date.humanize()})"
                await evt.respond(response)

