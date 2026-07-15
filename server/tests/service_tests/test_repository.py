from types import SimpleNamespace
import service.repository as repo
import pytest

def test_get_upload_bytes_by_id_reads_file(tmp_path, monkeypatch):
    # given
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    fname = "img.jpg"
    content = b"abc123"
    (uploads_dir / fname).write_bytes(content)

    # point the service at our temp dir
    monkeypatch.setattr(repo, "UPLOADS_PATH", str(uploads_dir))
    monkeypatch.setattr(repo, "get_upload_by_id", lambda uid: SimpleNamespace(id=uid, image_path=fname))

    # when
    result = repo.get_upload_bytes_by_id(1)

    assert result == content

def test_get_results_by_upload_id_returns_items(monkeypatch):
    items = [SimpleNamespace(title="t1", url="u1"), SimpleNamespace(title="t2", url="u2")]

    # patch the imported repository functions in service module
    monkeypatch.setattr(repo, "get_query_by_upload_id", lambda _: SimpleNamespace(id=42, search_keyword="k"))
    monkeypatch.setattr(repo, "get_items_by_query_id", lambda _: items)

    res = repo.get_results_by_upload_id(7)
    assert res == items

def test_get_upload_bytes_by_id_throws_if_file_missing(tmp_path, monkeypatch):
    # given
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir() # Empty folder, file 'missing.jpg' is not created here
    fname = "missing.jpg"

    monkeypatch.setattr(repo, "UPLOADS_PATH", str(uploads_dir))
    monkeypatch.setattr(repo, "get_upload_by_id", lambda uid: SimpleNamespace(id=uid, image_path=fname))

    # when / then
    with pytest.raises(FileNotFoundError) as exc_info:
        repo.get_upload_bytes_by_id(1)
        
    assert "Image file missing from disk" in str(exc_info.value)

def test_get_results_by_upload_id_when_query_does_not_exist(monkeypatch):
    # given: mock returns None instead of a Query object
    monkeypatch.setattr(repo, "get_query_by_upload_id", lambda uid: None)

    # when / then
    with pytest.raises(AttributeError):
        repo.get_results_by_upload_id(7)