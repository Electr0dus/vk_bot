from dotenv import load_dotenv
import os

from vkbottle.bot import Bot, Message


load_dotenv()

bot = Bot(token=os.getenv('API_KEY'))


@bot.on.message(text="Hello")
async def hi_handler(message: Message):
    user_info = await bot.api.users.get(message.from_id)
    if user_info:
        user = user_info[0].first_name
    else:
        user = 'незнакомец'
    await message.answer(f"Hello! {user}")
    print(user_info)


if __name__ == '__main__':
    bot.run_forever()