from sqlalchemy import delete
from telebot.types import PollAnswer

from . import telegram_bot
from models.event import Source
from models.poll import Poll
from models.user import SourceUnsubscription
from repository import session


def _sources_to_unsubscribe(poll_options, selected_option_ids) -> set[Source]:
    """Return the sources the user did *not* select in the poll (pure)."""
    selected = {
        poll_option.source
        for poll_option in poll_options
        if poll_option.id in selected_option_ids
    }
    return set(Source) - selected


@telegram_bot.poll_answer_handler()
def handle_source_poll_answer(poll_answer: PollAnswer):  # pragma: no cover - DB storage
    user_id = poll_answer.user.id

    poll = session.get(Poll, poll_answer.poll_id)
    sources_to_unsubscribe = _sources_to_unsubscribe(
        poll.poll_options, poll_answer.option_ids
    )
    source_unsubscriptions = [
        SourceUnsubscription(source=source, user_id=user_id)
        for source in sources_to_unsubscribe
    ]
    # delete existing unsubscriptions
    stmt = delete(SourceUnsubscription).where(SourceUnsubscription.user_id == user_id)
    session.execute(stmt)
    # add new unsubscriptions
    session.add_all(source_unsubscriptions)
    session.commit()
