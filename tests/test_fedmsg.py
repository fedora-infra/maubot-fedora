# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: MIT

import asyncio
from unittest import mock

import pytest
from fedora_messaging import exceptions as fm_exceptions
from maubot_fedora_messages import GiveCookieV1

from fedora import fedmsg


@pytest.fixture
def dummy_cookie():
    return {
        "sender": "dummy-user",
        "recipient": "foobar",
        "fedora_release": "39",
        "total": 1,
        "count_by_release": {"39": 1},
    }


def test__publish(monkeypatch, dummy_cookie):
    api_publish = mock.Mock()
    monkeypatch.setattr("fedora_messaging.api.publish", api_publish)
    fedmsg._publish(GiveCookieV1(dummy_cookie))
    api_publish.assert_called_once()


def test__publish_with_errors(monkeypatch, dummy_cookie):
    api_publish = mock.Mock()
    api_publish.side_effect = fm_exceptions.ConnectionException()
    monkeypatch.setattr("fedora_messaging.api.publish", api_publish)
    with pytest.raises(fm_exceptions.ConnectionException):
        fedmsg._publish(GiveCookieV1(dummy_cookie))
    assert api_publish.call_count == 3


async def test_publish(monkeypatch, dummy_cookie):
    api_publish = mock.Mock()
    monkeypatch.setattr("fedora_messaging.api.publish", api_publish)
    message = GiveCookieV1(dummy_cookie)
    await fedmsg.publish(message)
    await asyncio.gather(*fedmsg._background_tasks)
    api_publish.assert_called_once()
