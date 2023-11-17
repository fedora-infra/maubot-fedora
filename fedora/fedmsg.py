import asyncio
import logging
import sys
import traceback

import backoff
from fedora_messaging import api, message
from fedora_messaging import exceptions as fm_exceptions

log = logging.getLogger(__name__)


def backoff_hdlr(details):
    log.warning("Publishing message failed. Retrying. %s", traceback.format_tb(sys.exc_info()[2]))


def giveup_hdlr(details):
    log.error("Publishing message failed. Giving up. %s", traceback.format_tb(sys.exc_info()[2]))


@backoff.on_exception(
    backoff.expo,
    (fm_exceptions.ConnectionException, fm_exceptions.PublishException),
    max_tries=3,
    on_backoff=backoff_hdlr,
    on_giveup=giveup_hdlr,
)
def _publish(message: message.Message):
    api.publish(message)


_background_tasks = set()


async def publish(message: message.Message):
    loop = asyncio.get_running_loop()
    # Fire and forget
    # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
    fut = loop.run_in_executor(None, _publish, message)
    _background_tasks.add(fut)
    # To prevent keeping references to finished tasks forever, make each task
    # remove its own reference from the set after completion:
    fut.add_done_callback(_background_tasks.discard)
