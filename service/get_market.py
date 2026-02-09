import asyncio
from config import API
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
                print("Новый товар найден!")
                print(newest.title)
                print(newest.description)
                print(int(newest.price.amount)/100, newest.price.currency.name)
                print(f"https://vk.com/market-{GROUP_ID}?w=product-{GROUP_ID}_{newest.id}")
                last_know_item_id = newest.id
        await asyncio.sleep(30)
