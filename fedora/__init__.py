import logging
from itertools import chain

from maubot import MessageEvent, Plugin
from maubot.handlers import command
from mautrix.util.async_db import UpgradeTable
from mautrix.util.config import BaseProxyConfig

from .bugzilla import BugzillaHandler
from .clients.fasjson import FasjsonClient
from .config import Config
from .constants import ALIASES, NL
from .db import upgrade_table
from .distgit import DistGitHandler
from .fas import FasHandler
from .oncall import OnCallHandler
from .pagureio import PagureIOHandler

log = logging.getLogger(__name__)


class Fedora(Plugin):
    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable:
        return upgrade_table

    async def start(self) -> None:
        self.config.load_and_update()
        self.fasjsonclient = FasjsonClient(self.config["fasjson_url"])
        self.register_handler_class(PagureIOHandler(self.config))
        self.register_handler_class(DistGitHandler(self.config))
        self.register_handler_class(FasHandler(self.fasjsonclient))
        self.register_handler_class(BugzillaHandler(self.config))
        self.register_handler_class(OnCallHandler(self.config, self.database, self.fasjsonclient))

    async def stop(self) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> type[BaseProxyConfig]:
        return Config

    def _get_handler_commands(self):
        for cmd, _ignore in chain(*self.client.event_handlers.values()):
            if not isinstance(cmd, command.CommandHandler):
                continue
            func_mod = cmd.__mb_func__.__module__
            if func_mod != __name__ and not func_mod.startswith(f"{__name__}."):
                continue
            yield cmd

    @command.new(name="help", help="list commands")
    @command.argument("commandname", pass_raw=True, required=False)
    async def bothelp(self, evt: MessageEvent, commandname: str) -> None:
        """return help"""
        output = []

        if commandname:
            # return the full help (docstring) for the given command
            for cmd in self._get_handler_commands():
                aliases = ALIASES.get(cmd.__mb_name__, [])
                if commandname != cmd.__mb_name__ and commandname not in aliases:
                    continue
                output.append(cmd.__mb_full_help__)
                aliases = ALIASES.get(commandname, []) or aliases
                if aliases:
                    output.append(f"{NL}#### Aliases ####")
                    for alias in aliases:
                        output.append(f"* `{alias}`")
                break
            else:
                await evt.reply(f"`{commandname}` is not a valid command")
                return
        else:
            # list all the commands with the help arg from command.new
            for cmd in self._get_handler_commands():
                output.append(
                    f"* `{cmd.__mb_prefix__} {cmd.__mb_usage_args__}` - {cmd.__mb_help__}"
                )
        await evt.respond(NL.join(output))

    @command.new(help="return information about this bot")
    async def version(self, evt: MessageEvent) -> None:
        """
        Return the version of the plugin

        Takes no arguments
        """

        await evt.respond(f"maubot-fedora version {self.loader.meta.version}")
