"""`redact` — la valeur rédigée et les chemins rédigés, sur une structure imbriquée."""

from journal.redact import REDACTED, redact


def test_redacts_nested_structure_and_reports_every_path():
    payload = {
        "repo": "pithos_campaign",
        "auth": {"api_key": "ghp_secret", "user": "victorcarre"},
        "calls": [{"url": "https://api", "bot_token": "1234:abcd"}],
    }

    projection, paths = redact(payload)

    assert projection["auth"]["api_key"] == REDACTED
    assert projection["calls"][0]["bot_token"] == REDACTED
    assert paths == ["$.auth.api_key", "$.calls[0].bot_token"]


def test_keeps_every_non_secret_value_intact():
    payload = {
        "repo": "pithos_campaign",
        "auth": {"api_key": "ghp_secret", "user": "victorcarre"},
        "calls": [{"url": "https://api", "bot_token": "1234:abcd"}],
    }

    projection, _ = redact(payload)

    assert projection["repo"] == "pithos_campaign"
    assert projection["auth"]["user"] == "victorcarre"
    assert projection["calls"][0]["url"] == "https://api"


def test_a_name_that_merely_contains_key_is_not_a_secret():
    payload = {
        "monkey": 1,
        "keynote": 2,
        "hockey": 3,
    }

    projection, paths = redact(payload)

    assert projection == payload
    assert paths == []


def test_separators_and_case_do_not_hide_a_secret():
    payload = {
        "GITHUB-TOKEN": "x",
        "Telegram_Bot_Token": "y",
        "AWS_SECRET_ACCESS_KEY": "z",
    }

    _, paths = redact(payload)

    assert paths == ["$.GITHUB-TOKEN", "$.Telegram_Bot_Token", "$.AWS_SECRET_ACCESS_KEY"]


def test_a_secret_subtree_is_replaced_whole_and_never_traversed():
    payload = {"credentials": {"user": "victorcarre", "password": "hunter2"}}

    projection, paths = redact(payload)

    assert projection == {"credentials": REDACTED}
    assert paths == ["$.credentials"]


def test_a_tuple_is_projected_as_a_list_with_indexed_paths():
    payload = {"pair": ("public", {"token": "t"})}

    projection, paths = redact(payload)

    assert projection == {"pair": ["public", {"token": REDACTED}]}
    assert paths == ["$.pair[1].token"]
