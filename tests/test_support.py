from tests.support import load_double


def test_each_double_load_has_independent_state():
    first = load_double("journal")
    second = load_double("journal")
    first.disk_full = True
    first.events.append("first only")
    assert first is not second
    assert second.disk_full is False
    assert second.events == []


def test_loading_a_double_preserves_its_public_interface():
    double = load_double("kernel")
    node = double.node()
    assert node.id == "node-1"
    assert node.criterion.symbols == ["f"]
