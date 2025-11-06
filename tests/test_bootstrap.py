from project_empathy.bootstrap import create_schema, seed_demo_data
from project_empathy.config import get_settings
from project_empathy.db import SessionLocal, reset_engine_cache
from project_empathy.models import MenuItem, Order, Reservation, Restaurant, Subscription


def test_seed_demo_creates_turnkey_dataset(tmp_path, monkeypatch):
    db_path = tmp_path / "demo.db"
    monkeypatch.setenv("EMP_DATABASE__URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()  # type: ignore[attr-defined]
    reset_engine_cache()

    create_schema()

    with SessionLocal() as session:
        created = seed_demo_data(session=session, skip_existing=True)
        session.flush()
        assert created is True
        assert session.query(Restaurant).count() == 1
        assert session.query(MenuItem).count() >= 4
        assert session.query(Order).count() == 1
        assert session.query(Reservation).count() == 1
        assert session.query(Subscription).count() == 1

        # Second call should be idempotent when skip_existing=True
        assert seed_demo_data(session=session, skip_existing=True) is False

    # Running without session should work (internal session management)
    assert seed_demo_data(skip_existing=False) is True
