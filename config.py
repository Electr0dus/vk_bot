from dotenv import load_dotenv
import os
from vkbottle import PhotoMessageUploader
from vkbottle import API, BuiltinStateDispenser
from vkbottle.bot import BotLabeler


load_dotenv()

api = API(os.getenv('API_KEY'))
labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()


uploader = PhotoMessageUploader(api)
