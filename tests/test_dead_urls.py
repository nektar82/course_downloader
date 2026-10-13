"""Dead URL store tests."""

from pathlib import Path

from course_downloader.dead_urls import DeadUrlStore


def test_mark_and_check_dead(tmp_path: Path) -> None:
    store = DeadUrlStore(tmp_path / "dead-urls.json")
    assert not store.is_dead("https://example.com/gone")

    store.mark_dead("https://example.com/gone")
    assert store.is_dead("https://example.com/gone")
    assert len(store) == 1


def test_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "dead-urls.json"
    store = DeadUrlStore(path)
    store.mark_dead("https://example.com/gone")

    store2 = DeadUrlStore(path)
    assert store2.is_dead("https://example.com/gone")


def test_handles_missing_and_corrupt_file(tmp_path: Path) -> None:
    # Missing file: empty store, no crash.
    store = DeadUrlStore(tmp_path / "nope.json")
    assert len(store) == 0

    # Corrupt file: empty store, no crash.
    bad = tmp_path / "bad.json"
    bad.write_text("not json{{{", encoding="utf-8")
    store2 = DeadUrlStore(bad)
    assert len(store2) == 0
