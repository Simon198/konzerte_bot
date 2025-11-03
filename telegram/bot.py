from repository import session

from . import telegram_bot
from .callback_query_handler import handle_callback_query
from .message_handler import handle_message
from .poll_answer_handler import handle_poll_answer


def run_telegram_bot():
    offset = None
    while True:
        updates = telegram_bot.get_updates(offset=offset, timeout=5)
        if len(updates) == 0:
            break

        for update in updates:

            if update.message is not None:
                handle_message(update.message)
            elif update.poll_answer is not None:
                handle_poll_answer(update.poll_answer)
            elif update.callback_query is not None:
                handle_callback_query(update.callback_query)
            else:
                # TODO: what to do
                print()

            session.commit()
            offset = max(update.update_id + 1, offset or 0)

        print()
    print()
