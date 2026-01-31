from vkbottle.bot import BotLabeler, Message, rules
from vkbottle_types.objects import MessagesConversation

'''Бот должен быть добавлен в чат'''
class ChatInfoRule(rules.ABCRule[Message]):
    async def check(self, message: Message) -> dict:
        chat_info = await message.ctx_api.messages.get_conversations_by_id(
            peer_ids=[message.peer_id]  # peer_ids должен быть списком
        )
        if chat_info.items:
            return {"chat": chat_info.items[0]}
        return {"chat": None}  # Возвращаем None если чат не найден



chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True
chat_labeler.auto_rules = [rules.PeerRule(from_chat=True), ChatInfoRule()]


@chat_labeler.message(command="самобан")
async def kick(message: Message, chat: MessagesConversation):
    # await message.ctx_api.messages.remove_chat_user(message.chat_id, message.from_id)
    await message.answer(f"Участник самоустранился из {chat.chat_settings.title} по собственному желанию")


@chat_labeler.message(text="где я")
async def where_am_i(message: Message, chat: MessagesConversation):
    if chat and chat.chat_settings:
        await message.answer(f"Вы в <<{chat.chat_settings.title}>>")
    else:
        await message.answer("Информация о чате не найдена")

@chat_labeler.message(text="привет")
async def hello(message: Message):
    await message.answer("И тебе привет!")