from vkbottle import API, VKAPIError
from vkbottle.http import AiohttpClient
from vkbottle.bot import Message
import asyncio
from typing import List, Optional, Union
from database import Session, SavedMessage
from service.down_img import download_image
from config import api

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


async def get_all_members(group_id: int | str):

    all_members = []
    offset = 0
    count_per_request = 1000  # максимум за один запрос

    try:
        while True:
            response = await api.groups.get_members(
                group_id=group_id,
                count=count_per_request,
                offset=offset,
                # fields="sex,city,..."   ← можно добавить, если нужны поля
                # sort="id_asc"           ← или "time_asc", "time_desc"
            )

            if not response.items:
                break

            all_members.extend(response.items)  # это уже list[int] — id участников

            print(f"Собрано {len(all_members)} участников...")
            offset += count_per_request

            # Защита от слишком частых запросов
            await asyncio.sleep(0.35)

        print(f"Всего найдено участников: {len(all_members)}")
        return all_members
    except VKAPIError as e:
        print(f"Ошибка VK API: {e}")
        return []


async def send_message_to_users(user_ids: List[int], text: str, attachment: Optional[Union[str, List[str]]] = None):
    """Отправка сообщения пользователям"""
    for user_id in user_ids:
        try:
            await api.messages.send(
                user_id=user_id,
                message=text,
                attachment=attachment,
                random_id=0  # random_id должен быть уникальным для каждого сообщения
            )
            print(f"Сообщение отправлено пользователю {user_id}")
            await asyncio.sleep(0.35)
        except VKAPIError as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")