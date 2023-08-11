from typing import Type, Union
import inspect

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

import fasjson_client

from maubot import Plugin, MessageEvent
from maubot.handlers import command, event


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("fasjson_url")
        helper.copy("accounts_baseurl")
        helper.copy("botname")

class Fedora(Plugin):
    def _userlink(self, username: str) -> str:
        """
        Returns a markdown string with the link to the accounts
        for that user
        """
        return f"[{username}]({self.config['accounts_baseurl']}user/{username})"

    def _get_person_by_username(self, username: str) -> Union[dict, str]:
        """looks up a user by the username"""
        try:
            person = self.fasjsonclient.get_user(username=username).result
        except fasjson_client.errors.APIError as e:
            if e.code == 404:
                return f"Sorry, but user '{username}' does not exist"
            else:
                return "Something blew up, please try again"

        return person

    def _get_group_members(self, groupname: str) -> Union[list, str]:
        """looks up a group members by the groupname"""
        try:
            members = self.fasjsonclient.list_group_members(groupname=groupname).result
        except fasjson_client.errors.APIError as e:
            if e.code == 404:
                return f"Sorry, but group '{groupname}' does not exist"
            else:
                self.log.error(e)
                return "Something blew up, please try again"
        return members
    
    def _get_group_sponsors(self, groupname: str) -> Union[list, str]:
        """looks up a group sponsors by the groupname"""
        try:
            sponsors = self.fasjsonclient.list_group_sponsors(groupname=groupname).result
        except fasjson_client.errors.APIError as e:
            if e.code == 404:
                return f"Sorry, but group '{groupname}' does not exist"
            else:
                self.log.error(e)
                return "Something blew up, please try again"
        return sponsors


    async def start(self) -> None:
        self.config.load_and_update()
        self.log.debug("Loaded %s from config example 2", self.config["fasjson_url"])
        try:
            self.fasjsonclient = fasjson_client.Client(
                url=self.config["fasjson_url"],
            )
        except fasjson_client.errors.ClientSetupError as e:
            self.log.error(
                "Something went wrong setting up "
                "fasjson client with error: %s" % e
            )

    async def stop(self) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @command.new(name="help", help=f"list commands")
    @command.argument("commandname", pass_raw=True, required=False)
    async def bothelp(self, evt: MessageEvent, commandname: str) -> None:
        """return help"""

        if commandname:
            # return the full help (docstring) for the given command
            for c, commandobject in inspect.getmembers(self):
                if commandname == c:
                    output = commandname
                    await evt.respond(f"{inspect.getdoc(commandobject.__mb_func__)}")
                    self.log.error(inspect.getmembers(commandobject))
                    return
            
            await evt.respond(f"`{commandname}` is not a valid command")
            return
        else:
            # list all the commands with the help arg from command.new
            output = ""
            for c, commandobject in inspect.getmembers(self):
                if isinstance(commandobject, command.CommandHandler):
                    # generate arguments string
                    arguments = ""
                    for argument in commandobject.__mb_arguments__:
                        if argument.required:
                            arguments = f"{arguments} <{argument.name}>"
                        else:
                            arguments = f"{arguments} [{argument.name}]"
                    output = output+ f"`!{commandobject.__mb_name__} {arguments}`:: {commandobject.__mb_help__}      \n"
            await evt.respond(output)


    @command.new(help="bork bork bork and plugin version")
    async def swedish(self, evt: MessageEvent) -> None:
        """
        Return the version of the plugin

        Takes no arguments
        """

        await evt.respond("kwack kwack")
        await evt.respond("bork bork bork")
        await evt.respond(f"maubot-fedora version {self.loader.meta.version}")

    @command.new(help="Return a list of members of the specified group")
    @command.argument("groupname", pass_raw=True, required=True)
    async def members(self, evt: MessageEvent, groupname: str) -> None:
        """
        Return a list of the members of the Fedora Accounts group

        ## Arguments ##
        `groupname`: (required) The name of the Fedora Accounts group
        """
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!members designteam`")
            return

        members = self._get_group_members(groupname)

        if isinstance(members, str):
            await evt.respond(members)
        else:
            await evt.respond(f"Members of {groupname}: {', '.join(self._userlink(m['username']) for m in members)}")

    @command.new(help="Return a list of owners of the specified group")
    @command.argument("groupname", pass_raw=True, required=True)
    async def sponsors(self, evt: MessageEvent, groupname: str) -> None:
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!sponsors designteam`")
            return

        sponsors = self._get_group_sponsors(groupname)

        if isinstance(sponsors, str):
            await evt.respond(sponsors)
        else:
            await evt.respond(f"Sponsors of {groupname}: {', '.join(self._userlink(s['username']) for s in sponsors)}")
