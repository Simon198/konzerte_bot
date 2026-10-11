"""Integration tests for ``telegram.poll_answer_handler``."""

import types

import pytest
from sqlalchemy import select

from models.event import Source
from models.poll import Poll, PollOption
from models.user import SourceUnsubscription
from telegram import poll_answer_handler

pytestmark = pytest.mark.integration


class TestHandleSourcePollAnswer:
    def test_persists_unsubscriptions(self, wire):
        wire(poll_answer_handler)
        poll = Poll(id=1)
        for index, source in enumerate(Source):
            poll.poll_options.append(PollOption(id=index, source=source))
        poll_answer_handler.session.add(poll)
        poll_answer_handler.session.commit()

        poll_answer = types.SimpleNamespace(
            user=types.SimpleNamespace(id=1),
            poll_id=1,
            option_ids=[0, 1],
        )
        poll_answer_handler.handle_source_poll_answer(poll_answer)

        subs = poll_answer_handler.session.scalars(
            select(SourceUnsubscription).where(SourceUnsubscription.user_id == 1)
        ).all()
        assert {s.source for s in subs} == {Source.JAHRHUNDERTHALLE, Source.SCHLACHTHOF}
