import pytest
from personal_chatbot.src.memory_manager import InMemoryStore, MemoryRecord, MemoryError


def test_create_and_get_record_roundtrip():
    store = InMemoryStore()
    rec = MemoryRecord(id="r1", user_id="u1", content="hello", metadata={"k": "v"})
    store.create(rec)

    fetched = store.get("r1")
    assert fetched is not None
    assert fetched.id == "r1"
    assert fetched.user_id == "u1"
    assert fetched.content == "hello"
    assert fetched.metadata == {"k": "v"}


def test_duplicate_create_raises():
    store = InMemoryStore()
    rec = MemoryRecord(id="r1", user_id="u1", content="a", metadata={})
    store.create(rec)
    with pytest.raises(MemoryError):
        store.create(rec)


def test_list_by_user_with_limit():
    store = InMemoryStore()
    # Two for u1, one for u2
    store.create(MemoryRecord(id="1", user_id="u1", content="a", metadata={}))
    store.create(MemoryRecord(id="2", user_id="u1", content="b", metadata={}))
    store.create(MemoryRecord(id="3", user_id="u2", content="c", metadata={}))

    results = store.list_by_user("u1", limit=1)
    assert len(results) == 1
    assert results[0].user_id == "u1"


def test_delete_records():
    store = InMemoryStore()
    store.create(MemoryRecord(id="1", user_id="u1", content="a", metadata={}))
    assert store.delete("1") is True
    assert store.get("1") is None
    # Deleting non-existing returns False
    assert store.delete("1") is False