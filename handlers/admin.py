from vkbottle.bot import BotLabeler, Message, rules
from database import Session, SavedMessage
from service.down_img import download_image
admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(118331657)] # ID пользователя

# Состояния пользователей (для обработки пошаговых команд)
user_states = {}


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


@admin_labeler.message.on.message()
async def handle_message(message: Message):
    user_id = message.from_id

    if user_id in user_states:
        state = user_states[user_id]

        if state['awaiteng_text']:
            text = message.text

            state['text'] = text
            state['awaiting_text'] = False
            state['awaiting_photo'] = True

            if message.attachments:
                for attachment in message.attachments:
                    if attachment.photo:
                        photo = attachment.photo
                        sizes = photo.sizes
                        largest = max(sizes, key=lambda s: s.width*s.height)

                        state['photo_url'] = largest.url

                        with Session() as session:
                            saved_msg = SavedMessage(
                                user_id=user_id,
                                text=text,
                                image_url=largest.url,
                                image_path=''
                            )
                            session.add(saved_msg)
                            session.commit()

                            # Сохраняем локально
                            filename = f'photo_{saved_msg.id}.jpg'
                            filepath = await download_image(largest.url, filename)
                            if filepath:
                                saved_msg.image_path = filepath
                                session.commit()

                        await message.answer(
                            f'✅ Сообщение сохранено!\n'
                            f'ID: {saved_msg.id}\n'
                            f'Текст: {text[:100]}...\n'
                            f'Картинка сохранена'
                        )

                        del user_states[user_id]
                        return
                await message.answer(
                    f'Текст сохранен: {text[:100]...\n}'
                    'Теперь отправьте картинку (или напишите 'без фото')'
                )
            elif state["awaiting_photo"]:
            # Обработка картинки или текста "без фото"
            if message.text and message.text.lower() == 'без фото':
                # Сохраняем без фото
                with Session() as session:
                    saved_msg = SavedMessage(
                        user_id=user_id,
                        text=state["text"]
                    )
                    session.add(saved_msg)
                    session.commit()

                await message.answer(
                    f"✅ Сообщение сохранено без фото!\n"
                    f"ID: {saved_msg.id}\n"
                    f"Текст: {state['text'][:100]}..."
                )

                del user_states[user_id]
                return

            # Проверяем вложения
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.photo:
                        photo = attachment.photo
                        sizes = photo.sizes
                        largest = max(sizes, key=lambda s: s.width * s.height)

                        # Сохраняем в базе данных
                        with Session() as session:
                            saved_msg = SavedMessage(
                                user_id=user_id,
                                text=state["text"],
                                image_url=largest.url
                            )
                            session.add(saved_msg)
                            session.commit()

                            # Сохраняем локально
                            filename = f"photo_{saved_msg.id}.jpg"
                            filepath = await download_image(largest.url, filename)
                            if filepath:
                                saved_msg.image_path = filepath
                                session.commit()

                        await message.answer(
                            f"✅ Сообщение сохранено!\n"
                            f"ID: {saved_msg.id}\n"
                            f"Текст: {state['text'][:100]}...\n"
                            f"Картинка сохранена"
                        )

                        del user_states[user_id]
                        return

            await message.answer(
                "Пожалуйста, отправьте картинку или напишите 'без фото'"
            )



# TODO: Сделать команду для запуска рассылки
