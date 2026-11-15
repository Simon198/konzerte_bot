"""Integration tests for ``repository``."""

import pytest

import repository
from models.user import User

pytestmark = pytest.mark.integration


class TestWithDbSession:
    def test_returns_result(self, session, monkeypatch):
        monkeypatch.setattr(repository, "session", session)

        @repository.with_db_session
        def ok():
            return "result"

        assert ok() == "result"

    def test_rolls_back_and_reraises_on_error(self, session, monkeypatch):
        monkeypatch.setattr(repository, "session", session)

        @repository.with_db_session
        def boom():
            session.add(User(id=999, chat_id=999))
            session.flush()
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            boom()

        # The pending insert was rolled back by ``with_db_session``.
        assert session.get(User, 999) is None


class TestConfigureSqlite:
    def test_applies_pragmas_on_connect(self):
        with repository.engine.connect() as conn:
            foreign_keys = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
            busy_timeout = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()

        assert foreign_keys == 1
        assert busy_timeout == 30000
