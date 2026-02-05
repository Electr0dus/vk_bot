import aiohttp
import os


async def download_image(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                os.makedirs('images', exist_ok=True)
                filepath = f'images/{filename}'
                with open(filepath, 'wb') as f:
                    f.write(await response.read())
                return filepath
    return None