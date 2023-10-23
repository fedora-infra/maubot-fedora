from __future__ import annotations

from maubot import MessageEvent
from maubot.handlers import command

from .handler import Handler

"""
Old zodbot had a lot of fun little gags.
Why not carry (some of) them over?
"""


class MiscHandler(Handler):
    @command.new(name="fire")
    @command.argument("firee", required=True)
    async def fire(self, evt: MessageEvent, firee: str) -> None:
        await evt.mark_read()
        await evt.react("🔥")
        await evt.reply(f"adamw fires {firee}")

    @command.new(name="cake")
    async def cake(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        await evt.react("🍰")
        await evt.reply(f"here {evt.sender}, take your slice of cake")

    @command.new(name="beefymiracle")
    async def beefymiracle(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        await evt.react("🌭")
        await evt.reply("ALL HAIL THE BEEFY MIRACLE!! (The mustard indicates progress)")
