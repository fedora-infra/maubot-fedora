import re
from typing import TypeGuard

from maubot import MessageEvent
from mautrix.types import BaseMessageEventContent, MessageType, Obj, TextMessageEventContent
from mautrix.util.async_db import Scheme

from .clients.fasjson import FasjsonClient
from .constants import FAS_MATRIX_DOMAINS, MATRIX_USER_RE
from .exceptions import InfoGatherError

MENTION_RE = re.compile(r"href=['\"]?http[s]?://matrix.to/#/([^'\" >]+)['\" >]")


def get_matrix_id(username: str, evt: MessageEvent):
    # else check if the username given is a matrix id (@<username>:<server.com>)
    if MATRIX_USER_RE.match(username):
        return username

    # check if the formatted message has mentions (ie the user has tab-completed on someones
    # name) in them
    if is_text_message(evt.content) and evt.content.formatted_body:
        # in element at least, when usernames are mentioned, they are formatted like:
        # <a href="https://matrix.to/#/@zodbot:fedora.im">zodbot</a>
        # here we check the formatted message and extract all the matrix user IDs
        matches = MENTION_RE.findall(evt.content.formatted_body)
        if len(matches) > 1:
            raise InfoGatherError("Sorry, I can only look up one username at a time")
        elif len(matches) == 1:
            return matches[0]

    # No match, username is not a matrix ID already
    if " " in username:
        raise InfoGatherError("Sorry, I can only look up one username at a time")

    return None


async def get_fasuser_from_matrix_id(matrix_id: str, fasjson: FasjsonClient):
    try:
        return await fasjson.get_users_by_matrix_id(matrix_id)
    except InfoGatherError:
        # Matrix ID not set in FAS, only use it if it's on fedora.im.
        matrix_user_match = MATRIX_USER_RE.match(matrix_id)
        # return await fasjson.get_user(matrix_user_match.group(1))
        if matrix_user_match is not None and matrix_user_match.group(2) in FAS_MATRIX_DOMAINS:
            username = matrix_user_match.group(1)
            return await fasjson.get_user(username)
        else:
            raise


async def get_fasuser(username: str, evt: MessageEvent, fasjson: FasjsonClient):
    matrix_id = get_matrix_id(username, evt)
    if matrix_id:
        user = await get_fasuser_from_matrix_id(matrix_id, fasjson)
        if user is not None:
            return user
    # We haven't found a matrix ID.
    # Assume we were given a FAS / Fedora Account ID and use that
    return await fasjson.get_user(username)


def get_rowcount(db, result):
    if db.scheme == Scheme.POSTGRES:
        return int(result.split(" ")[-1])
    else:
        return result.rowcount


def matrix_ids_from_ircnicks(ircnicks):
    mxids = []
    for nick in ircnicks or []:
        if nick.startswith("matrix://"):
            # should be "matrix://matrix.org/username"
            m = nick.replace("matrix://", "").split("/")
            # m should be ['matrix.org', "username"]
            mxids.append(f"@{m[1]}:{m[0]}")
        elif nick.startswith("matrix:/"):
            mxids.append(f"{nick.replace('matrix:/', '@')}:fedora.im")
    return mxids


def tag_user(mxid, name=None):
    return f"[{name or mxid}](https://matrix.to/#/{mxid})"


def is_text_message(content: BaseMessageEventContent | Obj) -> TypeGuard[TextMessageEventContent]:
    """
    Check that a message's content is an instance of TextMessageEventContent
    and of msgtype TEXT or NOTICE
    """
    return (
        isinstance(content, TextMessageEventContent)
        # TextMessageEventContent can also be of MessageType.EMOTE, hence the second check
        and content.msgtype in {MessageType.TEXT, MessageType.NOTICE}
    )
