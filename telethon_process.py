import os
import json
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, User
from telethon.errors import *
import datetime
import random
from typing import List, Tuple
from tracking import UserTracker
from config import ACCOUNTS, PROXIES, ACCOUNT_SETTINGS

# Файлы для обмена данными
command_file = 'command.json'
result_file = 'result.json'

# Инициализация трекера
tracker = UserTracker()

# Словарь для хранения клиентов
clients = {}


class AdditionResult:
    def __init__(self):
        self.successful_users: List[str] = []
        self.failed_users: List[str] = []
        self.total_attempted: int = 0
        self.start_time: datetime.datetime = datetime.datetime.now()
        self.end_time: datetime.datetime = None

    def complete(self):
        self.end_time = datetime.datetime.now()

    @property
    def duration(self) -> datetime.timedelta:
        end = self.end_time or datetime.datetime.now()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        if not self.total_attempted:
            return 0.0
        return len(self.successful_users) / self.total_attempted * 100


async def get_or_create_client(account):
    phone = account['phone']

    if phone not in clients:
        device_model = f"Samsung Galaxy S{random.randint(20, 23)}"
        system_version = f"Android {random.randint(10, 13)}.0"

        try:
            proxy = account['proxy']
            client = TelegramClient(
                f'session_{phone}',
                account['api_id'],
                account['api_hash'],
                device_model=device_model,
                system_version=system_version,
                app_version="10.0.0",
                proxy={
                    'proxy_type': proxy['scheme'],
                    'addr': proxy['hostname'],
                    'port': proxy['port'],
                    'username': proxy['username'],
                    'password': proxy['password'],
                    'rdns': True
                }
            )

            print(f"🔄 Подключение к аккаунту {phone} через прокси {proxy['hostname']}")
            await client.connect()

            if not await client.is_user_authorized():
                print(f"⚠️ Требуется авторизация для {phone}")
                await client.start(phone)

            clients[phone] = client
            print(f"✅ Клиент создан для {phone}")

        except Exception as e:
            print(f"❌ Ошибка создания клиента для {phone}: {str(e)}")
            raise e

    return clients[phone]


async def send_result(chat_id, message):
    with open(result_file, 'w') as file:
        json.dump({"chat_id": chat_id, "data": message}, file)


async def verify_user_added(client, channel, user) -> bool:
    try:
        participants = await client.get_participants(
            channel,
            search=user.username,
            limit=1
        )
        return bool(participants and participants[0].id == user.id)
    except Exception as e:
        print(f"❌ Ошибка при проверке добавления {user.username}: {str(e)}")
        return False


async def add_users_to_channel(
        client,
        source_entity,
        target_entity,
        users_to_add: List[User],
        phone: str
) -> AdditionResult:
    result = AdditionResult()
    result.total_attempted = len(users_to_add)

    for user in users_to_add:
        try:
            if not isinstance(user, User) or not user.username:
                result.failed_users.append(f"{user.id} (нет username)")
                continue

            await client(InviteToChannelRequest(
                target_entity,
                [user]
            ))

            # Проверяем успешность добавления
            if await verify_user_added(client, target_entity, user):
                result.successful_users.append(user.username)
            else:
                result.failed_users.append(f"{user.username} (не подтверждено)")

            await asyncio.sleep(random.uniform(2, 4))

        except (UserPrivacyRestrictedError, UserNotMutualContactError,
                UserBannedInChannelError, FloodWaitError) as e:
            result.failed_users.append(f"{user.username} ({str(e)})")
        except Exception as e:
            print(f"❌ Ошибка добавления {user.username}: {str(e)}")
            result.failed_users.append(f"{user.username} (ошибка)")

        # Проверяем лимиты
        account_stats = tracker.get_account_status(phone)
        if account_stats['total_added'] >= 50:
            break

    result.complete()
    return result


async def get_valid_participants(client, channel, limit: int = 50) -> List[User]:
    participants = []
    offset = 0

    while len(participants) < limit:
        try:
            chunk = await client(GetParticipantsRequest(
                channel,
                ChannelParticipantsSearch(''),
                offset,
                limit=100,
                hash=0
            ))

            if not chunk.users:
                break

            for user in chunk.users:
                if (isinstance(user, User) and
                        user.username and
                        not user.bot and
                        not user.deleted and
                        len(participants) < limit):
                    participants.append(user)

            offset += len(chunk.users)

        except Exception as e:
            print(f"❌ Ошибка получения участников: {str(e)}")
            break

    return participants


async def add_user_to_channel(account, source_channel, target_channel, chat_id):
    phone = account['phone']

    try:
        client = await get_or_create_client(account)

        source_entity = await client.get_entity(source_channel)
        target_entity = await client.get_entity(target_channel)

        account_stats = tracker.get_account_status(phone)
        remaining_capacity = account_stats['remaining_capacity']

        if remaining_capacity <= 0:
            await send_result(chat_id, f"""
❌ Аккаунт {phone} достиг лимита
⏳ Следующее добавление через:
{account_stats['time_remaining']['hours']}ч {account_stats['time_remaining']['minutes']}м
""")
            return 0

        all_participants = await get_valid_participants(
            client,
            source_entity,
            min(50, remaining_capacity)
        )

        if not all_participants:
            await send_result(chat_id, "❌ Нет подходящих пользователей")
            return 0

        total_added = 0
        batches = [all_participants[i:i + 25] for i in range(0, len(all_participants), 25)]

        for batch_num, batch in enumerate(batches, 1):
            addition_result = await add_users_to_channel(
                client,
                source_entity,
                target_entity,
                batch,
                phone
            )

            successful_count = len(addition_result.successful_users)
            total_added += successful_count

            tracker.record_addition(phone, successful_count, target_channel)
            status = tracker.get_account_status(phone)

            report = f"""
✅ Группа {batch_num}/{len(batches)} обработана
📱 Аккаунт: {phone}

📊 Результаты:
• Успешно: {successful_count}/{len(batch)}
• Неудачно: {len(addition_result.failed_users)}
• Всего: {total_added}/{len(all_participants)}
• Успешность: {addition_result.success_rate:.1f}%
• Время: {addition_result.duration.seconds}с

🔄 Статус аккаунта:
• Всего добавлено: {status['total_added']}/50
• Осталось: {status['remaining_capacity']}
• За 24ч: {status['last_24h_adds']}

⏳ Следующее добавление через:
{status['time_remaining']['hours']}ч {status['time_remaining']['minutes']}м {status['time_remaining']['seconds']}с

❌ Ошибки добавления:
{chr(10).join(addition_result.failed_users[:5])}
{f'...и еще {len(addition_result.failed_users) - 5}' if len(addition_result.failed_users) > 5 else ''}
"""
            await send_result(chat_id, report)

            if batch_num < len(batches):
                await send_result(chat_id, f"⏳ Пауза {ACCOUNT_SETTINGS['delay_between_adds']} секунд...")
                await asyncio.sleep(ACCOUNT_SETTINGS['delay_between_adds'])

        return total_added

    except Exception as e:
        await send_result(chat_id, f"❌ Ошибка: {str(e)}")
        return 0


async def get_channel_info(channel_username, chat_id, account):
    try:
        client = await get_or_create_client(account)
        channel = await client.get_entity(channel_username)
        full_channel = await client(GetFullChannelRequest(channel))

        # Получаем всех участников с username
        valid_participants = []
        total_checked = 0

        await send_result(chat_id, "🔄 Идет подсчет пользователей с username...")

        async for participant in client.iter_participants(channel):
            total_checked += 1
            if participant.username:
                valid_participants.append(participant)

            if total_checked % 1000 == 0:
                progress = (total_checked / full_channel.full_chat.participants_count) * 100
                await send_result(chat_id, f"""
🔄 Проверено: {total_checked}/{full_channel.full_chat.participants_count}
📊 Прогресс: {progress:.1f}%
✅ Найдено с username: {len(valid_participants)}
""")

        users_with_username = len(valid_participants)

        # Расчет времени с учетом всех аккаунтов
        users_per_day = len(ACCOUNTS) * 100  # 8 аккаунтов * 50 пользователей * 2 раза в день
        days_needed = users_with_username / users_per_day
        hours_needed = days_needed * 24

        full_days = int(days_needed)
        remaining_hours = int((days_needed - full_days) * 24)

        info = f"""
📊 Информация о канале {channel_username}:

👥 Участники:
• Всего участников: {full_channel.full_chat.participants_count}
• С username: {users_with_username}
• Процент доступных: {(users_with_username / full_channel.full_chat.participants_count * 100):.1f}%
  (только пользователи с username могут быть добавлены)

📝 Данные канала:
• ID: {channel.id}
• Название: {channel.title}
• Приватный: {'Да' if channel.username is None else 'Нет'}

💡 Расчет времени добавления:
• Доступно аккаунтов: {len(ACCOUNTS)}
• Добавлений в день: {users_per_day} пользователей
  ({len(ACCOUNTS)} аккаунтов × 50 пользователей × 2 раза в день)
• Примерное время: {full_days} дней {remaining_hours} часов
  (с учетом всех аккаунтов и пауз)

⚠️ Важно:
• Каждый аккаунт добавляет 50 человек за цикл
• После добавления нужна пауза 12 часов
• Каждый аккаунт может сделать 2 цикла в сутки
"""
        await send_result(chat_id, info)

    except Exception as e:
        await send_result(chat_id, f"❌ Ошибка: {str(e)}")


async def monitor_command_file():
    while True:
        try:
            if os.path.exists(command_file) and os.path.getsize(command_file) > 0:
                with open(command_file, 'r') as file:
                    command_data = json.load(file)

                if command_data.get('command') == "add_user_to_channel":
                    total_added = 0
                    successful_accounts = 0
                    accounts = [acc for acc in ACCOUNTS if acc['phone'] in command_data.get('accounts', [])]

                    for i, account in enumerate(accounts):
                        added = await add_user_to_channel(
                            account=account,
                            source_channel=command_data['source_channel'],
                            target_channel=command_data['target_channel'],
                            chat_id=command_data['chat_id']
                        )

                        if added > 0:
                            total_added += added
                            successful_accounts += 1

                        if i < len(accounts) - 1:
                            await send_result(
                                command_data['chat_id'],
                                f"⏳ Пауза {ACCOUNT_SETTINGS['delay_between_accounts']} секунд..."
                            )
                            await asyncio.sleep(ACCOUNT_SETTINGS['delay_between_accounts'])

                    overall_stats = tracker.get_overall_stats()
                    summary = f"""
{'✅' if successful_accounts > 0 else '⚠️'} Процесс завершен!

📊 Результаты:
• Добавлено: {total_added} пользователей
• Успешных аккаунтов: {successful_accounts}/{len(accounts)}
• За 24 часа: {overall_stats['total_added_24h']}
• Всего: {overall_stats['total_added_all_time']}

📱 Доступно аккаунтов: {overall_stats['accounts_available']}/{len(ACCOUNTS)}
"""
                    await send_result(command_data['chat_id'], summary)

                elif command_data.get('command') == "get_channel_info":
                    await get_channel_info(
                        command_data['channel'],
                        command_data['chat_id'],
                        command_data['account']
                    )

                open(command_file, 'w').close()

            await asyncio.sleep(1)

        except Exception as e:
            print(f"Ошибка мониторинга команд: {str(e)}")
            await asyncio.sleep(5)


async def main():
    print("✅ Telethon процесс запущен")
    await monitor_command_file()


if __name__ == "__main__":
    asyncio.run(main())
