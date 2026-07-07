from types import SimpleNamespace
import service.repository as svc


def test_get_upload_bytes_by_id_reads_file(tmp_path, monkeypatch):
    # prepare uploads dir and file
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    fname = "img.jpg"
    content = b"abc123"
    (uploads_dir / fname).write_bytes(content)

    # point the service at our temp dir
    monkeypatch.setattr(svc, "UPLOADS_PATH", str(uploads_dir))

    # patch the repository call to return an object with image_path attribute
    monkeypatch.setattr(svc, "get_upload_by_id", lambda uid: SimpleNamespace(id=uid, image_path=fname))

    result = svc.get_upload_bytes_by_id(1)
    assert result == content


def test_get_results_by_upload_id_returns_items(monkeypatch):
    items = [SimpleNamespace(title="t1", url="u1"), SimpleNamespace(title="t2", url="u2")]

    # patch the imported repository functions in service module
    monkeypatch.setattr(svc, "get_query_by_upload_id", lambda uid: SimpleNamespace(id=42, search_keyword="k"))
    monkeypatch.setattr(svc, "get_items_by_query_id", lambda qid: items)

    res = svc.get_results_by_upload_id(7)
    assert res == [vars(item) for item in items]
