
from vkbottle.bot import BotLabeler, Message, rules
from database import Session, SavedMessage
from service.send_msg import handle_text_input, handle_photo_input
import os
from service.send_msg import user_states, VKGroupSender
from config import uploader
from dotenv import load_dotenv

admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(118331657)] # ID пользователя


load_dotenv()
# Состояния пользователей (для обработки пошаговых команд)
global user_states
global uploader


@admin_labeler.message(command="halt")
async def halt(_):
    '''Остановить работу бота'''
    exit(0)


@admin_labeler.message(command="msg_send")
async def start_message_send(message: Message):
    user_id = message.from_id
    user_states[user_id] = {"awaiting_text": True,
                            "awaiteng_photo": False}

    await message.answer('Отправьте текст сообщения, которое хотите запустить в рассылку.\n'
                         'После текста вы можете прикрепить картинку.'
                        )


@admin_labeler.message(command='msg_list')
async def list_messages(message: Message):
    '''
    Вывод в сообщение список всех сохранённых сообщений

    '''
    with Session() as session:
        messages = session.query(SavedMessage).order_by(SavedMessage.id.desc()).limit(10).all()

        if not messages:
            await message.answer("Сохранённых сообщений нет")
            return

        response = "📋 Последние сохраненные сообщения:\n\n"
        for msg in messages:
            has_photo = "✅" if msg.image_url else "❌"
            response += f"ID: {msg.id}\n"
            response += f"Текст: {msg.text[:50]}...\n"
            response += f"Фото: {has_photo}\n"
            response += f"Дата: {msg.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            response += "─" * 30 + "\n"

        await message.answer(response)


@admin_labeler.message(text="/msg_get <msg_id>")
async def get_message(message: Message, msg_id: str):
    try:
        msg_id_int = int(msg_id)
    except ValueError:
        await message.answer("ID сообщения должен быть числом")
        return

    with Session() as session:
        saved_msg = session.query(SavedMessage).filter_by(id=msg_id_int).first()

        if not saved_msg:
            await message.answer(f"Сообщение с ID {msg_id} не найдено")
            return

        msg_id = saved_msg.id
        created_at = saved_msg.created_at.strftime('%d.%m.%Y %H:%M')
        user_id = saved_msg.user_id
        text = saved_msg.text
        image_url = saved_msg.image_url
        image_path = saved_msg.image_path

        await message.answer(
            f"📄 Сообщение #{msg_id}\n"
            f"📅 Дата: {created_at}\n"
            f"👤 От: {user_id}\n\n"
            f"{text}"
        )

        if image_url:
            # try:
            attachment = await uploader.upload(file_source=image_path)
            await message.answer("📎 Прикрепленная картинка:", attachment=attachment)
            # except Exception as e:
            #     await message.answer(f"Не удалось загрузить картинку: {str(e)}")


@admin_labeler.message(text="/msg_delete <msg_id>")
async def delete_message(message: Message, msg_id: str):
    '''
    Функция для удаления сохранённого сообщения по ID. Команда: /msg_delete <ID>
    '''
    try:
        msg_id_int = int(msg_id)
    except ValueError:
        await message.answer("ID сообщения должен быть числом")
        return

    with Session() as session:
        saved_msg = session.query(SavedMessage).filter_by(id=msg_id_int).first()

        if not saved_msg:
            await message.answer(f"Сообщение с ID {msg_id} не найдено")
            return

        if saved_msg.image_path and os.path.exists(saved_msg.image_path):
            os.remove(saved_msg.image_path)

        session.delete(saved_msg)
        session.commit()

        await message.answer(f'✅ Сообщение с ID {msg_id} удалено')


@admin_labeler.message(text="/send_user <msg_id>")
async def send_user_msg(message: Message, msg_id: str):
    '''
    Отправка сообщения из БД одному пользователю
    '''
    try:
        msg_id_int = int(msg_id)
    except ValueError:
        await message.answer("ID сообщения должен быть числом")
        return
    with Session() as session:
        saved_msg = session.query(SavedMessage).filter_by(id=msg_id_int).first()

        if not saved_msg:
            await message.answer(f"Сообщение с ID {msg_id} не найдено")
            return

        msg_id = saved_msg.id
        created_at = saved_msg.created_at.strftime('%d.%m.%Y %H:%M')
        user_id = saved_msg.user_id
        text = saved_msg.text
        image_url = saved_msg.image_url
        image_path = saved_msg.image_path

        TOKEN = os.getenv('API_KEY')  # Токен группы

        sender = VKGroupSender(TOKEN)

        if image_path:
            attachment = await uploader.upload(file_source=image_path)
            await sender.send_message('118331657', text, attachment=attachment)
            return

        await sender.send_message('118331657', text)


@admin_labeler.message(text="/send_all <msg_id>")
async def send_all_user(message: Message, msg_id: str):
    '''
    Запустить рассылку для всех пользователей
    '''
    try:
        msg_id_int = int(msg_id)
    except ValueError:
        await message.answer("ID сообщения должен быть числом")
        return
    with Session() as session:
        saved_msg = session.query(SavedMessage).filter_by(id=msg_id_int).first()

        if not saved_msg:
            await message.answer(f"Сообщение с ID {msg_id} не найдено")
            return

        msg_id = saved_msg.id
        created_at = saved_msg.created_at.strftime('%d.%m.%Y %H:%M')
        user_id = saved_msg.user_id
        text = saved_msg.text
        image_url = saved_msg.image_url
        image_path = saved_msg.image_path

        TOKEN = os.getenv('API_KEY')  # Токен группы

        sender = VKGroupSender(TOKEN)
        GROUP_ID = os.getenv('ID_GROUP')  # ID группы (только цифры)

        if image_path:
            attachment = await uploader.upload(file_source=image_path)
            await sender.broadcast(GROUP_ID, text, attachment=attachment)
            return

        await sender.broadcast(GROUP_ID, text)


@admin_labeler.message()
async def handle_message(message: Message):
    user_id = message.from_id

    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state["awaiting_text"]:
        await handle_text_input(message, state, user_id)
    elif state["awaiting_photo"]:
        await handle_photo_input(message, state, user_id)

# TODO: сделать автоматическую рассылку, когда добавляется новая карточка товара в сообщетсве
