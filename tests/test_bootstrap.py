from pathlib import Path

from project_empathy.bootstrap import create_schema, seed_demo_data
from project_empathy.config import get_settings
from project_empathy.db import SessionLocal, reset_engine_cache
from project_empathy.models import MenuItem, Order, Reservation, Restaurant, Subscription


def test_seed_demo_creates_turnkey_dataset(tmp_path, monkeypatch):
    db_path = tmp_path / "demo.db"
    data_dir = tmp_path / "storage"
    monkeypatch.setenv("EMP_DATABASE__URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("EMP_STORAGE__DATA_DIR", str(data_dir))
    monkeypatch.setenv("EMP_STORAGE__TRANSCRIPTS_DIR", str(data_dir / "transcripts"))
    get_settings.cache_clear()  # type: ignore[attr-defined]
    reset_engine_cache()

    create_schema()

    with SessionLocal() as session:
        result = seed_demo_data(session=session, skip_existing=True)
        session.flush()
        assert result.created is True
        assert result.api_key
        assert session.query(Restaurant).count() == 1
        assert session.query(MenuItem).count() >= 4
        assert session.query(Order).count() == 1
        assert session.query(Reservation).count() == 1
        assert session.query(Subscription).count() == 1

        # Second call should be idempotent when skip_existing=True
        second = seed_demo_data(session=session, skip_existing=True)
        assert second.created is False

    stored_key = Path(data_dir / "demo_api_key.txt")
    assert stored_key.exists()
    first_key = stored_key.read_text().strip()
    assert first_key == result.api_key

    # Running without session should work (internal session management)
    third = seed_demo_data(skip_existing=False)
    assert third.created is True
    assert stored_key.read_text().strip() == third.api_key
