import httpx
import pytest

import fedora

from .bot import make_message


@pytest.mark.parametrize(
    "username,mention,expected",
    [
        ("", None, "dummy"),
        ("dummy", None, "dummy"),
        ("dummy2", None, "dummy2"),
        ("@dummy:example.com", None, "dummy"),
        ("@dummy2:example.com", None, "dummy2"),
        ("Dummy", "@dummy:fedora.im", "dummy"),
        ("Dummy2", "@dummy2:example.com", "dummy2"),
        ("dummy", "@foobar:somewhere.com", "dummy"),
        ("DisplayName", "@dummy:example.com", None),
    ],
)
async def test_get_fasuser(bot, plugin, respx_mock, username, mention, expected):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={"result": {"username": "dummy"}},
        )
    )
    respx_mock.get("http://fasjson.example.com/v1/users/dummy2/").mock(
        return_value=httpx.Response(
            200,
            json={"result": {"username": "dummy2"}},
        )
    )
    respx_mock.get("http://fasjson.example.com/v1/users/DisplayName/").mock(
        return_value=httpx.Response(404, json={"result": None})
    )
    no_result = httpx.Response(200, json={"result": []})
    # User dummy hasn't set their matrix ID in FAS
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy"},
    ).mock(return_value=no_result)
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://somewhere.com/foobar"},
    ).mock(return_value=no_result)
    # But user dummy2 has
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy2"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"username": "dummy2"}]},
        )
    )

    message = make_message(f"!hello {username}")
    if mention:
        message.content.formatted_body = f'<p>!hello <a href="https://matrix.to/#/{mention}"></p>'
    if expected is None:
        with pytest.raises(fedora.exceptions.InfoGatherError) as exc:
            result = await fedora.utils.get_fasuser(username, message, plugin.fasjsonclient)
        assert str(exc.value) == f"Sorry, but Fedora Accounts user '{username}' does not exist"
    else:
        result = await fedora.utils.get_fasuser(username, message, plugin.fasjsonclient)
        assert result["username"] == expected
