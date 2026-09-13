"""Identité de résultat contre identité de transport — décision 30."""

from broker.identity import Effect, new_identity, result_key, same_result, transport_key


def test_result_key_is_stable_across_attempts_of_the_same_effect():
    first = result_key("mission-1", "node-7", 2, Effect.notify)
    second = result_key("mission-1", "node-7", 2, Effect.notify)
    assert first == second and len(first) == 64


def test_result_key_separates_every_axis():
    base = result_key("mission-1", "node-7", 2, Effect.notify)
    others = [
        result_key("mission-2", "node-7", 2, Effect.notify),
        result_key("mission-1", "node-8", 2, Effect.notify),
        result_key("mission-1", "node-7", 3, Effect.notify),
        result_key("mission-1", "node-7", 2, Effect.pull_request),
    ]
    assert base not in others and len(set(others)) == 4


def test_axes_cannot_be_confused_by_concatenation():
    left = result_key("mission-1", "node-7", 2, Effect.notify)
    right = result_key("mission", "1node-7", 2, Effect.notify)
    assert left != right


def test_transport_key_is_renewed_at_every_call():
    assert transport_key() != transport_key()


def test_a_retry_keeps_the_result_and_renews_the_transport():
    first = new_identity("mission-1", "node-7", 2, Effect.notify)
    retry = new_identity("mission-1", "node-7", 2, Effect.notify)
    assert same_result(first, retry)
    assert first.transport != retry.transport


def test_a_further_attempt_is_another_result():
    first = new_identity("mission-1", "node-7", 2, Effect.notify)
    later = new_identity("mission-1", "node-7", 3, Effect.notify)
    assert not same_result(first, later)
