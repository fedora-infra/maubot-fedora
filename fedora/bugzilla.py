from maubot import MessageEvent
from maubot.handlers import command

from .clients.bugzilla import BugzillaClient


class BugzillaHandler:
    def __init__(self, config):
        self.config = config
        self.bugzillaclient = BugzillaClient("https://bugzilla.redhat.com")

    @command.new(help="return a bugzilla bug")
    @command.argument("bug_id", required=True)
    async def bug(self, evt: MessageEvent, bug_id: str) -> None:
        if not bug_id:
            await evt.respond("bug_id argument is required. e.g. `!bug 1234567`")
            return
        result = await self.bugzillaclient.get_bug(bug_id)
        await evt.respond(
            f"[RHBZ#{bug_id}](https://bugzilla.redhat.com/{bug_id}): {result['bugs'][0]['summary']}"
        )
