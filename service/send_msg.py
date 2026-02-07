from vkbottle import API
from vkbottle.http import AiohttpClient
from vkbottle.bot import Message
import asyncio
from typing import List, Optional, Union
from database import Session, SavedMessage
from service.down_img import download_image



class VKGroupSender:
    def __init__(self, token: str):
        # Создаем HTTP клиент
        http_client = AiohttpClient()
        # Инициализируем API
        self.api = API(token=token, http_client=http_client)

    async def get_all_members(self, group_id: str, limit: int = None) -> List[int]:
        """Получить всех участников группы"""
        members = []
        offset = 0
        count = 1000  # Максимум за запрос

        print("Начинаем сбор участников группы...")

        while True:
            # Получаем участников партиями
            response = await self.api.request(
                "groups.getMembers",
                {
                    "group_id": group_id,
                    "offset": offset,
                    "count": count,
                    "fields": "can_write_private_message",
                    "v": "5.199"  # Указываем версию API
                }
            )
            if not response.get("response", {}).get("items"):
                break
            items = response["response"]["items"]
            for member in items:
                # Проверяем, можно ли писать пользователю
                if member.get("can_write_private_message", 1) == 1:
                    members.append(member["id"])
            print(f"Получено {len(items)} пользователей, всего {len(members)}")
            # Если указан лимит
            if limit and len(members) >= limit:
                members = members[:limit]
                break
            # Если получено меньше count, значит это последняя партия
            if len(items) < count:
                break
            offset += count
            await asyncio.sleep(0.3)  # Задержка для избежания лимитов

        return members

    async def upload_photo(self, photo_path: str) -> Optional[str]:
        """Загружает фотографию на сервер VK и возвращает attachment строку"""

        # Получаем адрес сервера для загрузки
        upload_server = await self.api.request(
            "photos.getMessagesUploadServer",
            {
                "v": "5.199"
            }
        )

        upload_url = upload_server["response"]["upload_url"]

        # Загружаем файл на сервер
        with open(photo_path, 'rb') as file:
            files = {'photo': file}
            async with AiohttpClient() as session:
                async with session.post(upload_server["response"]["upload_url"], data=files) as response:
                    upload_result = await response.json()

        # Сохраняем фото на сервере VK
        save_result = await self.api.request(
            "photos.saveMessagesPhoto",
            {
                "photo": upload_result["photo"],
                "server": upload_result["server"],
                "hash": upload_result["hash"],
                "v": "5.199"
            }
        )

        if save_result.get("response"):
            photo = save_result["response"][0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            if 'access_key' in photo:
                attachment += f"_{photo['access_key']}"
            return attachment
        return None

    async def send_message(self, user_id: int, message: str,
                           attachment: Optional[List[str]] = None) -> bool:
        """Отправить сообщение пользователю с возможностью прикрепления фото"""

        # Подготавливаем параметры для отправки
        params = {
            "user_id": user_id,
            "message": message,
            "random_id": 0,
            "v": "5.199"
        }
        # Добавляем вложения, если они есть
        if attachment:
            params["attachment"] = attachment
        await self.api.request("messages.send", params)
        print(f"Сообщение успешно отправлено пользователю {user_id}")
        return True

    async def broadcast(self, group_id: str, message: str,
                       attachment: Optional[List[str]] = None,
                       limit: int = None):
        """Основная функция рассылки с поддержкой фотографий"""

        # Получаем участников
        members = await self.get_all_members(group_id, limit)

        if not members:
            print("Не удалось получить участников группы")
            return

        print(f"Начинаем рассылку для {len(members)} пользователей...")
        print(f"Сообщение: {message}")

        success = 0
        failed = 0

        # Отправляем сообщения
        for i, user_id in enumerate(members):
            try:
                params = {
                    "user_id": user_id,
                    "message": message,
                    "random_id": 0,
                    "v": "5.199"
                }

                # Добавляем вложения, если они есть
                if attachment:
                    params["attachment"] = attachment

                await self.api.request("messages.send", params)
                success += 1
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")
                failed += 1

            # Выводим прогресс каждые 10 отправок
            if (i + 1) % 10 == 0:
                print(f"Прогресс: {i+1}/{len(members)} | Успешно: {success}")

            # Задержка для избежания лимитов (не более 20 сообщений в секунду)
            await asyncio.sleep(0.2)

        print(f"\nРассылка завершена!")
        print(f"Всего: {len(members)}")
        print(f"Успешно: {success}")
        print(f"Не удалось: {failed}")


user_states = {}


async def handle_text_input(message: Message, state: dict, user_id: int):
    """Обработка ввода текста"""
    text = message.text or ""
    if not text.strip():
        await message.answer("Пожалуйста, отправьте текст сообщения.")
        return

    state["text"] = text
    state["awaiting_text"] = False
    state["awaiting_photo"] = True

    # Если есть вложения, обрабатываем сразу
    if message.attachments:
        await save_message_with_photo(message, state, user_id)
        return

    await message.answer(
        f"Текст сохранен: {text[:100]}...\n"
        "Теперь отправьте картинку (или напишите 'без фото')"
    )


async def handle_photo_input(message: Message, state: dict, user_id: int):
    """Обработка ввода фото"""
    if message.text and message.text.lower() == 'без фото':
        await save_message_without_photo(state, user_id, message)
        return

    if message.attachments:
        await save_message_with_photo(message, state, user_id)
        return

    await message.answer("Пожалуйста, отправьте картинку или напишите 'без фото'")


async def save_message_with_photo(message: Message, state: dict, user_id: int):
    """Сохранение сообщения с фото"""
    photo_url = None
    image_path = ""

    # Ищем фото во вложениях
    for attachment in message.attachments:
        if attachment.photo:
            photo = attachment.photo
            sizes = photo.sizes
            largest = max(sizes, key=lambda s: s.width * s.height)
            photo_url = largest.url
            break

    if not photo_url:
        await message.answer("Не найдено фото во вложениях")
        return

    # Сохраняем в базу данных
    with Session() as session:
        saved_msg = SavedMessage(
            user_id=user_id,
            text=state["text"],
            image_url=photo_url,
            image_path=""
        )
        session.add(saved_msg)
        session.commit()

        # Получаем ID из БД
        msg_id = saved_msg.id
        msg_text = state["text"]

        # Сохраняем локально (опционально)
        if photo_url:
            try:
                filename = f"photo_{msg_id}.jpg"
                filepath = await download_image(photo_url, filename)
                if filepath:
                    saved_msg.image_path = filepath
                    session.commit()
            except Exception as e:
                print(f"Ошибка при сохранении файла: {e}")

    # Удаляем состояние пользователя
    del user_states[user_id]

    await message.answer(
        f"✅ Сообщение сохранено!\n"
        f"ID: {msg_id}\n"
        f"Текст: {msg_text[:100]}...\n"
        f"Картинка сохранена"
    )


async def save_message_without_photo(state: dict, user_id: int, message: Message):
    """Сохранение сообщения без фото"""
    with Session() as session:
        saved_msg = SavedMessage(
            user_id=user_id,
            text=state["text"]
        )
        session.add(saved_msg)
        session.commit()

        # Получаем данные до закрытия сессии
        msg_id = saved_msg.id
        msg_text = state["text"]

    # Удаляем состояние пользователя
    del user_states[user_id]

    await message.answer(
        f"✅ Сообщение сохранено без фото!\n"
        f"ID: {msg_id}\n"
        f"Текст: {msg_text[:100]}..."
    )



















from dotenv import load_dotenv
import os

load_dotenv()


# Использование
async def main():
    # Настройки
    TOKEN = os.getenv('API_KEY')  # Токен группы
    GROUP_ID = os.getenv('ID_GROUP')  # ID группы (только цифры)

    # Сообщение
    MESSAGE = """Приветствуем вас!

Мы рады сообщить о новом обновлении в нашей группе.

С уважением, Администрация"""

    # Вложения (необязательно)
    ATTACHMENTS = []  # Например: ["photo-123456_456239020"]

    # # Запуск
    sender = VKGroupSender(TOKEN)
    all_sub = []
    # all_sub = await sender.get_all_members(GROUP_ID)
    # await messenger.broadcast_message(
    #     group_id=GROUP_ID,
    #     message=MESSAGE,
    #     attachments=ATTACHMENTS,
    #     limit=50  # Для тестирования (уберите или закомментируйте для реальной рассылки)
    # )
    await sender.send_message('118331657', MESSAGE)
    # print(all_sub)

if __name__ == "__main__":
    asyncio.run(main())