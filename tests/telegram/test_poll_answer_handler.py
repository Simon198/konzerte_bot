"""Unit tests for ``telegram.poll_answer_handler``."""

from types import SimpleNamespace

from sqlalchemy import select

from models.event import Source
from models.poll import Poll, PollOption
from models.user import SourceUnsubscription
from telegram import poll_answer_handler


def _make_poll_answer(user_id=1, poll_id=1, option_ids=(0, 1)):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id),
        poll_id=poll_id,
        option_ids=list(option_ids),
    )


def _add_poll(session):
    poll = Poll(id=1)
    for index, source in enumerate(Source):
        poll.poll_options.append(PollOption(id=index, source=source))
    session.add(poll)
    session.commit()
    return poll


class TestHandleSourcePollAnswer:
    def test_unsubscribes_from_unselected_sources(self, session, monkeypatch):
        monkeypatch.setattr(poll_answer_handler, "session", session)
        _add_poll(session)

        poll_answer_handler.handle_source_poll_answer(
            _make_poll_answer(option_ids=[0, 1])
        )

        subs = session.scalars(
            select(SourceUnsubscription).where(SourceUnsubscription.user_id == 1)
        ).all()
        assert {s.source for s in subs} == {
            Source.JAHRHUNDERTHALLE,
            Source.SCHLACHTHOF,
        }

    def test_replaces_existing_unsubscriptions(self, session, monkeypatch):
        monkeypatch.setattr(poll_answer_handler, "session", session)
        _add_poll(session)
        session.add(SourceUnsubscription(source=Source.BATSCHKAPP, user_id=1))
        session.commit()

        # Selecting only Batschkapp -> unsubscribe from the other three sources.
        poll_answer_handler.handle_source_poll_answer(
            _make_poll_answer(option_ids=[0])
        )

        subs = session.scalars(
            select(SourceUnsubscription).where(SourceUnsubscription.user_id == 1)
        ).all()
        assert {s.source for s in subs} == {
            Source.FESTHALLE,
            Source.JAHRHUNDERTHALLE,
            Source.SCHLACHTHOF,
        }
