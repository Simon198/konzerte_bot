from tqdm.auto import tqdm as tqdm_auto

from telegram import ADMIN_CHAT_ID, admin_bot


class tqdm_admin_telegram(tqdm_auto):

    def __init__(self, *args, **kwargs):
        self.message_id = None
        self.last_text = None
        self.disable_notification = kwargs.get("disable_notification", True)
        super().__init__(*args, **kwargs)

    def display(self, **kwargs):
        super().display(**kwargs)
        fmt = self.format_dict
        if fmt.get("bar_format", None):
            fmt["bar_format"] = (
                fmt["bar_format"]
                .replace("<bar/>", "{bar:10u}")
                .replace("{bar}", "{bar:10u}")
            )
        else:
            fmt["bar_format"] = "{l_bar}{bar:10u}{r_bar}"

        formatted_text = self.format_meter(**fmt)
        if not formatted_text:
            formatted_text = "..."
        formatted_text = formatted_text.replace("\r", "").strip()
        if formatted_text == self.last_text:
            return
        self.last_text = formatted_text

        if self.message_id is None:
            message = admin_bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=formatted_text,
                disable_notification=self.disable_notification,
            )
            self.message_id = message.id
        else:
            admin_bot.edit_message_text(
                chat_id=ADMIN_CHAT_ID,
                message_id=self.message_id,
                text=formatted_text,
            )

    def clear(self, *args, **kwargs):
        super().clear(*args, **kwargs)

    def close(self):
        super().close()
