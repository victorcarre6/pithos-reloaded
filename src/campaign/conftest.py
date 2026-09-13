import pytest


@pytest.fixture
def bound(tmp_path, journal_double):
    from campaign import store

    path = tmp_path / "store.json"
    store.bind(path, trace=journal_double)
    yield path, journal_double
    store.bind(None, trace=journal_double)
