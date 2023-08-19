from typing import Type, Union
import inspect
import re

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

import fasjson_client

from maubot import Plugin, MessageEvent
from maubot.handlers import command, event


NL = "      \n"

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

    def catch_generic_fasjson_errors(func):
        def wrapper(self, *args, **kwargs):
            if self.fasjsonclient is None:
                # if the connection to FASJSON failed at plugin start, fasjsonclient will be None
                return f"Sorry, I can not give you the required information. I failed to connect to FASJSON on startup"
            try:
                return func(self, *args, **kwargs)
            except fasjson_client.errors.ClientSetupError as e:
                # typically this happens after the plugin starts up and runs for a while i.e. kerb ticket expires
                return f"Sorry, I can not give you the required information. I failed to connect to FASJSON: **{e}**"
            #except fasjson_client.errors.APIError as e:
                #return f"Sorry, I can not give you the required information. FASJSON returned API Error: **{e}**"

        return wrapper
    
    @catch_generic_fasjson_errors
    def _get_fasuser(self, username: str, evt: MessageEvent):
        def _get_person_by_username(username: str) -> dict | str:
            """looks up a user by the username"""
            try:
                person = self.fasjsonclient.get_user(username=username).result
            except fasjson_client.errors.APIError as e:
                if e.code == 404:
                    return f"Sorry, but Fedora Accounts user '{username}' does not exist"
            return person

        def _get_users_by_matrix_id(username: str) -> Union[dict, str]:
            """looks up a user by the matrix id"""
            
            # Fedora Accounts stores these strangly but this is to handle that
            try:
                matrix_username, matrix_server = re.findall(r'@(.*):(.*)',username)[0]
            except ValueError or IndexError:
                return f"Sorry, {username} does not look like a valid matrix user ID (e.g. @username:homeserver.com )"
        
            # if given a fedora.im address -- just look up the username as a FAS name
            if matrix_server == "fedora.im":
                return  _get_person_by_username(matrix_username)
            
            searchterm = f'matrix://{matrix_server}/{matrix_username}'
            searchresult = self.fasjsonclient.search(ircnick__exact=searchterm).result

            if len(searchresult) > 1:
                names = f"{NL}".join(name for name in searchresult) 
                return (f"{len(searchresult)} Fedora Accounts users have the {username} Matrix Account defined:{NL}"
                        f"{names}")
            elif len(searchresult) == 0:
                return f"No Fedora Accounts users have the {username} Matrix Account defined"
            
            return searchresult[0]

                
        # if no username is supplied, we use the matrix id of the sender (e.g. "@dudemcpants:fedora.im")
        if not username:
            username = evt.sender

        # check if the formatted message has mentions (ie the user has tab-completed on someones 
        # name) in them
        if evt.content.formatted_body:
            # in element at least, when usernames are mentioned, they are formatted like:
            # <a href="https://matrix.to/#/@zodbot:fedora.im">zodbot</a>
            # here we check the formatted message and extract all the matrix user IDs
            u = re.findall(r'href=[\'"]?http[s]?://matrix.to/#/([^\'" >]+)',evt.content.formatted_body)
            if len(u) > 1:
                return "Sorry, I can only look up one username at a time"
            elif len(u) == 1: 
                return _get_users_by_matrix_id(u[0])

        usernames = username.split(" ")
        if len(usernames) > 1:
            return "Sorry, I can only look up one username at a time"
        
        # else check if the username given is a matrix id (@<username>:<server.com>) 
        if re.search(r'@.*:.*',usernames[0]):
            return _get_users_by_matrix_id(usernames[0])
        
        # finally, assume we were given a FAS / Fedora Account ID and use that
        else:
            return _get_person_by_username(usernames[0])


    @catch_generic_fasjson_errors
    def _get_group_members(self, groupname: str) -> Union[list, str]:
        """looks up a group members by the groupname"""
        try:
            members = self.fasjsonclient.list_group_members(groupname=groupname).result
        except fasjson_client.errors.APIError as e:
            if e.code == 404:
                return f"Sorry, but group '{groupname}' does not exist"
        return members

    @catch_generic_fasjson_errors
    def _get_group_sponsors(self, groupname: str) -> Union[list, str]:
        """looks up a group sponsors by the groupname"""
        try:
            sponsors = self.fasjsonclient.list_group_sponsors(
                groupname=groupname
            ).result
        except fasjson_client.errors.APIError as e:
            if e.code == 404:
                return f"Sorry, but group '{groupname}' does not exist"
        return sponsors

    async def start(self) -> None:
        self.config.load_and_update()
        self.log.debug("Loaded %s from config example 2", self.config["fasjson_url"])
        try:
            self.fasjsonclient = fasjson_client.Client(
                url=self.config["fasjson_url"],
            )
        except fasjson_client.errors.ClientSetupError as e:
            self.fasjsonclient = None
            self.log.error(
                "Something went wrong setting up " "fasjson client with error: %s" % e
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
                    output = (
                        output
                        + f"`!{commandobject.__mb_name__} {arguments}`:: {commandobject.__mb_help__}      \n"
                    )
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
            await evt.respond(
                "groupname argument is required. e.g. `!members designteam`"
            )
            return

        members = self._get_group_members(groupname)

        if isinstance(members, str):
            await evt.respond(members)
        else:
            await evt.respond(
                f"Members of {groupname}: {', '.join(self._userlink(m['username']) for m in members)}"
            )

    @command.new(help="Return a list of owners of the specified group")
    @command.argument("groupname", pass_raw=True, required=True)
    async def sponsors(self, evt: MessageEvent, groupname: str) -> None:
        if not groupname:
            await evt.respond(
                "groupname argument is required. e.g. `!sponsors designteam`"
            )
            return

        sponsors = self._get_group_sponsors(groupname)

        if isinstance(sponsors, str):
            await evt.respond(sponsors)
        else:
            await evt.respond(
                f"Sponsors of {groupname}: {', '.join(self._userlink(s['username']) for s in sponsors)}"
            )

    @command.new(help="Return brief information about a Fedora user", aliases=['hi', 'hello', 'hello2'])
    @command.argument("username", pass_raw=True, required=False)
    async def hellomynameis(self, evt: MessageEvent, username: str) -> None:

        user = self._get_fasuser(username, evt)
        
        if isinstance(user, str):
            await evt.reply(user)
        else:
            await evt.reply(
                f"{user['human_name']} ({user['username']}) \<{user['emails'][0]}\>"
            )
