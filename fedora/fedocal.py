from maubot.handlers import command
from maubot import MessageEvent
from .clients.fedocal import FedocalClient
from .handler import Handler
from .constants import NL

class FedocalHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.fedocal_client = FedocalClient()

    @command.new(name="nextmeetings", help="Get the next 3 meetings")
    async def nextmeetings(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        
        room = evt.room_id
        
        nextthree_response = await self.fedocal_client.future_meetings()
        nextroom_response = await self.fedocal_client.next_room_meeting(room)

        response = f"The next meetings in FedoCal are:{NL}{nextthree_response}{nextroom_response}"
        await evt.respond(response)
        