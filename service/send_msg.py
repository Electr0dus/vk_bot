from vkbottle import API
from vkbottle.http import AiohttpClient
import asyncio
from typing import List


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

    async def send_message(self, user_id: int, message: str) -> bool:
        """Отправить сообщение пользователю"""
        try:
            await self.api.request(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": message,
                    "random_id": 0,
                    "v": "5.199"
                }
            )
            return True
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")
            return False

    async def broadcast(self, group_id: str, message: str, limit: int = None):
        """Основная функция рассылки"""

        # Получаем участников
        members = await self.get_all_members(group_id, limit)

        if not members:
            print("Не удалось получить участников группы")
            return

        print(f"Начинаем рассылку для {len(members)} пользователей...")

        success = 0
        failed = 0

        # Отправляем сообщения
        for i, user_id in enumerate(members):
            if await self.send_message(user_id, message):
                success += 1
            else:
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