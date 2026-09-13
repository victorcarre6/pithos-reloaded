"""Notifications sortantes, polling, offsets persistants, allowlist et signal d'interruption."""

from pathlib import Path

import pytest

from broker import telegram
from broker.telegram import Command, CommandKind, TelegramRequestRejected, TelegramTransportError
from broker.telegram import chunks, is_stale, note_failure, note_success, notify, poll
from broker.telegram import relay, remember_offset, retry_delay, saved_offset, u16len

OFFSETS = Path("telegram.json")


@pytest.fixture(autouse=True)
def pacing():
    "Le backoff et le registre d'envois sont partagés : chaque test repart de l'état neuf."

    note_success()
    telegram.sent.clear()

    yield

    note_success()
    telegram.sent.clear()


def update(update_id, text, sender=42, date=1000):
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "date": date,
            "text": text,
            "chat": {"id": 77},
            "from": {"id": sender},
        },
    }


class Controller:
    "Le contrôleur d'interruption d'`engine` vu depuis `broker` : un compteur, aucun arbre."

    def __init__(self):
        self.signals = 0

    def register_interrupt(self):
        self.signals += 1

        return "exit" if self.signals >= 2 else "interrupt"


# --- découpe en unités UTF-16 ---------------------------------------------

def test_a_short_text_is_a_single_chunk():
    assert chunks("bonjour") == ["bonjour"]


def test_an_emoji_counts_two_units_and_is_never_bisected():
    text = "🙂" * 3000
    pieces = chunks(text)
    assert all(u16len(piece) <= telegram.TEXT_LIMIT for piece in pieces)
    assert "".join(pieces) == text
    assert all(piece.count("�") == 0 for piece in pieces)


def test_the_limit_is_utf16_units_not_characters():
    text = "🙂" * 2049
    assert len(text) < telegram.TEXT_LIMIT < u16len(text)
    assert len(chunks(text)) == 2


# --- backoff monotone partagé ---------------------------------------------

def test_backoff_doubles_monotonically_up_to_the_ceiling():
    seen = []
    for _ in range(6):
        note_failure()
        seen.append(retry_delay())
    assert seen == [5, 10, 20, 40, 60, 60]


def test_any_successful_round_resets_the_backoff():
    note_failure()
    note_failure()
    note_success()
    assert retry_delay() == telegram.RETRY_INITIAL_SEC


def test_the_notifier_and_the_poller_share_one_backoff(api):
    api.scenario = lambda method, received: (500, {"ok": False, "description": "boom"})
    notify("sortie", "clé-1")
    before_poll = retry_delay()
    with pytest.raises(TelegramRequestRejected):
        poll(0)

    assert (before_poll, retry_delay()) == (5, 10)


# --- deux erreurs typées ---------------------------------------------------

@pytest.mark.parametrize("status, transient", [(429, True), (500, True), (400, False), (403, False)])
def test_an_explicit_negative_answer_is_a_rejection(api, status, transient):
    api.scenario = lambda method, received: (status, {"ok": False, "description": "nope"})
    with pytest.raises(TelegramRequestRejected) as failure:
        poll(0)
    assert failure.value.transient is transient


def test_an_unreadable_body_is_a_transport_error(api):
    api.scenario = lambda method, received: (200, "not an object")
    with pytest.raises(TelegramTransportError):
        poll(0)


def test_an_unreachable_route_is_a_transport_error(monkeypatch):
    monkeypatch.setenv("PITHOS_TELEGRAM_API", "http://127.0.0.1:1")
    monkeypatch.setenv("PITHOS_TELEGRAM_TOKEN", "test-token")
    with pytest.raises(TelegramTransportError):
        poll(0)


# --- notification sortante -------------------------------------------------

def test_notify_sends_the_text_to_the_configured_chat(api):
    assert notify("mission verte", "clé-1") is True
    method, payload = api.calls[0]
    assert (method, payload["chat_id"], payload["text"]) == ("sendMessage", "77", "mission verte")


def test_a_long_text_leaves_as_several_messages(api):
    assert notify("x" * 9000, "clé-1") is True
    assert [method for method, _ in api.calls] == ["sendMessage"] * 3


def test_replaying_the_same_key_never_sends_twice(api):
    notify("mission verte", "clé-1")
    assert notify("mission verte", "clé-1") is True
    assert len(api.calls) == 1


def test_a_transport_failure_is_reported_and_paces_the_next_try(api):
    api.scenario = lambda method, received: (503, {"ok": False, "description": "down"})
    assert notify("mission verte", "clé-1") is False
    assert retry_delay() == telegram.RETRY_INITIAL_SEC


def test_a_failed_send_is_not_remembered_as_sent(api):
    api.scenario = lambda method, received: (503, {"ok": False, "description": "down"})
    notify("mission verte", "clé-1")
    api.scenario = lambda method, received: (200, {"ok": True, "result": {"message_id": 1}})
    assert notify("mission verte", "clé-1") is True
    assert len(api.calls) == 2


def test_a_rejection_is_journalled_without_the_bot_token(api, trace, monkeypatch):
    monkeypatch.setattr(telegram, "journal", trace)
    echoed = "bad request to /bottest-token/sendMessage"
    api.scenario = lambda method, received: (400, {"ok": False, "description": echoed})
    assert notify("mission verte", "clé-1") is False
    recorded = trace.events[-1].payload["description"]
    assert "test-token" not in recorded and "***REDACTED***" in recorded


# --- polling, allowlist, offsets ------------------------------------------

def result(*updates):
    return lambda method, received: (200, {"ok": True, "result": list(updates)})


def test_poll_renders_the_five_commands(api):
    texts = ["/status", "/latest", "/pause", "/stop", "/answer oui"]
    api.scenario = result(*[update(index + 1, text) for index, text in enumerate(texts)])
    commands, offset = poll(0)
    assert [command.kind for command in commands] == list(CommandKind)
    assert offset == 6


def test_the_answer_command_carries_its_argument(api):
    api.scenario = result(update(1, "/answer oui, remplace le splice"))
    commands, _ = poll(0)
    assert (commands[0].kind, commands[0].argument) == (CommandKind.answer, "oui, remplace le splice")


def test_an_unknown_command_is_dropped(api):
    api.scenario = result(update(1, "/deploy now"), update(2, "bonjour"))
    commands, offset = poll(0)
    assert (commands, offset) == ([], 3)


def test_a_sender_outside_the_allowlist_is_ignored_and_journalled(api, trace, monkeypatch):
    monkeypatch.setattr(telegram, "journal", trace)
    api.scenario = result(update(1, "/stop", sender=99))
    commands, offset = poll(0)
    assert (commands, offset) == ([], 2)
    assert trace.events[-1].payload["sender"] == 99


def test_the_requested_offset_reaches_the_service(api):
    api.scenario = result()
    poll(41)
    assert api.calls[0][1]["offset"] == 41


def test_an_empty_round_keeps_the_offset(api):
    api.scenario = result()
    assert poll(41) == ([], 41)


def test_the_offset_survives_a_restart(trace):
    assert saved_offset(OFFSETS, trace=trace) == 0
    remember_offset(OFFSETS, 43, trace=trace)
    assert saved_offset(OFFSETS, trace=trace) == 43


# --- commande tardive et signal d'interruption ----------------------------

def test_a_command_older_than_the_mission_is_stale(api):
    api.scenario = result(update(1, "/stop", date=900))
    command = poll(0)[0][0]
    assert is_stale(command, 1000) is True
    assert is_stale(command, 800) is False


def test_pause_emits_one_signal_and_stop_reaches_the_exit(api):
    api.scenario = result(update(1, "/pause"), update(2, "/stop"))
    paused, stopped = poll(0)[0]

    controller = Controller()
    assert relay(paused, controller) == "interrupt"
    assert controller.signals == 1

    stopper = Controller()
    assert relay(stopped, stopper) == "exit"
    assert stopper.signals == 2


def test_a_read_only_command_emits_no_signal(api):
    api.scenario = result(update(1, "/status"))
    controller = Controller()
    assert relay(poll(0)[0][0], controller) is None
    assert controller.signals == 0
