from enum import Enum, auto


class CallbackData(Enum):
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CONSENT = "consent"
    GENRE = "genre"
    GENRE_DONE = "genre_done"
