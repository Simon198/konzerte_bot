from sqlalchemy import delete
from telebot.types import PollAnswer

from models.event import Source
from models.poll import Poll
from models.user import SourceUnsubscription
from repository import session


def sources_poll_answer(poll_answer: PollAnswer):
    user_id = poll_answer.user.id

    poll = session.get(Poll, poll_answer.poll_id)
    sources = set(
        poll_option.source
        for poll_option in poll.poll_options
        if poll_option.id in poll_answer.option_ids
    )
    sources_to_unsubscribe = set(Source) - sources
    source_unsubscriptions = [
        SourceUnsubscription(source=source, user_id=user_id)
        for source in sources_to_unsubscribe
    ]
    # delete existing unsubscriptions
    stmt = delete(SourceUnsubscription).where(SourceUnsubscription.user_id == user_id)
    session.execute(stmt)
    # add new unsubscriptions
    session.add_all(source_unsubscriptions)


def handle_poll_answer(poll_answer: PollAnswer):
    sources_poll_answer(poll_answer)
