import logging
from vkbottle import Bot
from config import api, state_dispenser, labeler
from handlers import chat_labeler, admin_labeler


file_log = logging.FileHandler("vkbot.log")
console_out = logging.StreamHandler()
format = "%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"

logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO, format=format)

labeler.load(chat_labeler)
labeler.load(admin_labeler)


bot = Bot(
    api=api,
    labeler=labeler,
    state_dispenser=state_dispenser,
)


bot.run_forever()
