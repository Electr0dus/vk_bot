import asyncio
from config import API, uploader
from service.send_msg import send_message_to_users
from service.down_img import download_image

from dotenv import load_dotenv
import os


load_dotenv()
last_know_item_id = None

USER_TOKEN = os.getenv("USER_TOKEN")

market_api = API(USER_TOKEN)


async def check_new_products():
    global last_know_item_id
    GROUP_ID = os.getenv("ID_GROUP")
    while True:
        res = await market_api.market.get(
            owner_id=-int(GROUP_ID),
            count=3,
            extended=1
        )
        if res.items:
            newest = res.items[0]
            if last_know_item_id is None:
                last_know_item_id = newest.id
            elif newest.id != last_know_item_id:
                msg: str = ""
                msg += (newest.title + '\n')
                msg += (newest.description + '\n')
                msg += f'{int(newest.price.amount)/100} {newest.price.currency.name}\n'
                msg += f'https://vk.com/market-{GROUP_ID}?w=product-{GROUP_ID}_{newest.id}'
                if newest.thumb_photo:
                    filepath = await download_image(newest.thumb_photo, f'photo_{newest.id}.jpg')
                    attachment = await uploader.upload(file_source=filepath)
                    await send_message_to_users([118331657], msg, attachment)
                    os.remove(filepath)
                else:
                    await send_message_to_users([118331657], msg)
                # print("Новый товар найден!")
                # print(newest.title)
                # print(newest.description)
                # print(int(newest.price.amount)/100, newest.price.currency.name)
                # print(f"https://vk.com/market-{GROUP_ID}?w=product-{GROUP_ID}_{newest.id}")

                last_know_item_id = newest.id
            # TODO: сделать рассылку пользователям в чат при получении нового товара, для начала сформирвоать красивую строку, чтобы было красиво, возможно научиться получать картинку товаора
            # чтоыб вместе с картинкой отправлять пользователю сообщение
        await asyncio.sleep(30)
