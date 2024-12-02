import os
import json
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, User
from telethon.errors import *
from telethon.tl.functions.messages import ExportChatInviteRequest
import datetime
import random
from typing import List, Tuple, Dict, Set, Optional
from tracking import UserTracker
from config import ACCOUNTS, PROXIES, ACCOUNT_SETTINGS

# Файлы для обмена данными
command_file = 'command.json'
result_file = 'result.json'

# Инициализация трекера
tracker = UserTracker()

# Словарь для хранения клиентов
clients = {}

class VerificationData:
    def __init__(self):
        self.initial_count: int = 0
        self.final_count: int = 0
        self.initial_members: Set[int] = set()
        self.final_members: Set[int] = set()
        self.join_events: List[int] = []
        self.verified_users: List[str] = []
        self.start_time: datetime.datetime = datetime.datetime.now()

    @property
    def count_difference(self) -> int:
        return self.final_count - self.initial_count

    @property
    def new_members(self) -> Set[int]:
        return self.final_members - self.initial_members

    @property
    def duration(self) -> float:
        return (datetime.datetime.now() - self.start_time).total_seconds()

class AdditionResult:
    def __init__(self):
        self.successful_users: List[str] = []
        self.failed_users: List[str] = []
        self.dm_sent: List[str] = []
        self.total_attempted: int = 0
        self.start_time: datetime.datetime = datetime.datetime.now()
        self.end_time: datetime.datetime = None
        self.verification_data: VerificationData = VerificationData()

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

async def send_invite_message(client, user, target_channel, invite_link):
    try:
        promo_text = f"""
Привет!
Присоединяйтесь к нашему каналу для швейников Бишкека ✂️: {target_channel}
Проверенные швейные цеха ✅
Полезные советы и рекомендации 💡
Тренды и новости 🧵
Экономьте время и находите надежных партнеров с нами!
👉 {'@impactsew_ru'}

С уважением,
Команда {target_channel}
"""
        await client.send_message(user.username, promo_text)
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки приглашения {user.username}: {str(e)}")
        return False


async def hybrid_verification(client, target_entity, result: AdditionResult):
    """Комплексная проверка добавления пользователей"""
    try:
        # Получаем конечное состояние
        final_channel = await client(GetFullChannelRequest(target_entity))
        result.verification_data.final_count = final_channel.full_chat.participants_count

        # Получаем список финальных участников
        final_participants = await client.get_participants(target_entity, limit=1000)
        result.verification_data.final_members = set(user.id for user in final_participants)

        # Проверяем каждого пользователя индивидуально
        verified_users = []
        for username in result.successful_users:
            if await verify_user_added(client, target_entity, username):
                verified_users.append(username)

        result.verification_data.verified_users = verified_users

        return {
            'verified_count': len(verified_users),
            'total_difference': result.verification_data.count_difference,
            'new_members': len(result.verification_data.new_members),
            'success_rate': (len(verified_users) / len(result.successful_users) * 100) if result.successful_users else 0
        }
    except Exception as e:
        print(f"❌ Ошибка верификации: {str(e)}")
        return None


async def add_users_to_channel(
        client,
        source_entity,
        target_entity,
        users_to_add: List[User],
        phone: str
) -> AdditionResult:
    result = AdditionResult()
    result.total_attempted = len(users_to_add)

    # Получаем начальное состояние
    try:
        initial_channel = await client(GetFullChannelRequest(target_entity))
        result.verification_data.initial_count = initial_channel.full_chat.participants_count

        initial_participants = await client.get_participants(target_entity, limit=1000)
        result.verification_data.initial_members = set(user.id for user in initial_participants)
    except Exception as e:
        print(f"❌ Ошибка получения начального состояния: {str(e)}")

    # Получаем пригласительную ссылку
    try:
        invite_link = await client(ExportChatInviteRequest(peer=target_entity))
        invite_url = invite_link.link
    except FloodWaitError as e:
        print(f"⏳ Flood wait: ждем {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"❌ Ошибка создания ссылки-приглашения: {str(e)}")
        invite_url = None

    # Регистрируем обработчик событий
    @client.on(events.ChatAction)
    async def handler(event):
        if event.user_joined:
            result.verification_data.join_events.append(event.user_id)

    for user in users_to_add:
        try:
            if not isinstance(user, User) or not user.username:
                result.failed_users.append(f"{user.id} (нет username)")
                continue

            # Пытаемся добавить пользователя
            await client(InviteToChannelRequest(
                target_entity,
                [user]
            ))

            # Проверяем успешность добавления
            if await verify_user_added(client, target_entity, user):
                result.successful_users.append(user.username)
            else:
                result.failed_users.append(f"{user.username} (не подтверждено)")
                # Пробуем отправить личное сообщение
                if invite_url and await send_invite_message(client, user, target_entity.username, invite_url):
                    result.dm_sent.append(user.username)

            await asyncio.sleep(random.uniform(2, 4))

        except (UserPrivacyRestrictedError, UserNotMutualContactError,
                UserBannedInChannelError, FloodWaitError) as e:
            result.failed_users.append(f"{user.username} ({str(e)})")
            # Пробуем отправить личное сообщение
            if invite_url and await send_invite_message(client, user, target_entity.username, invite_url):
                result.dm_sent.append(user.username)
        except Exception as e:
            print(f"❌ Ошибка добавления {user.username}: {str(e)}")
            result.failed_users.append(f"{user.username} (ошибка)")

        # Проверяем лимиты
        account_stats = tracker.get_account_status(phone)
        if account_stats['total_added'] >= 50:
            break

    # Даем время на обработку событий
    await asyncio.sleep(10)

    # Проводим финальную верификацию
    verification_results = await hybrid_verification(client, target_entity, result)

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

        # Получаем статус аккаунта
        account_stats = tracker.get_account_status(phone)
        remaining_capacity = account_stats['remaining_capacity']

        if remaining_capacity <= 0:
            await send_result(chat_id, f"""
❌ Аккаунт {phone} достиг лимита
⏳ Следующее добавление через:
{account_stats['time_remaining']['hours']}ч {account_stats['time_remaining']['minutes']}м
""")
            return 0

        # Собираем участников
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

            successful_count = len(addition_result.verification_data.verified_users)
            total_added += successful_count

            # Обновляем статистику
            tracker.record_addition(phone, successful_count, target_channel)
            status = tracker.get_account_status(phone)

            verification_stats = addition_result.verification_data

            report = f"""
✅ Группа {batch_num}/{len(batches)} обработана
📱 Аккаунт: {phone}

📊 Результаты добавления:
• Успешно подтверждено: {len(verification_stats.verified_users)}/{len(batch)}
• Не удалось добавить: {len(addition_result.failed_users)}
• Отправлено в ЛС: {len(addition_result.dm_sent)}
• Всего в этой сессии: {total_added}/{len(all_participants)}
• Успешность: {addition_result.success_rate:.1f}%
• Время выполнения: {addition_result.duration.seconds}с

📈 Верификация:
• Изначально в канале: {verification_stats.initial_count}
• Сейчас в канале: {verification_stats.final_count}
• Прирост: {verification_stats.count_difference}
• Новых участников: {len(verification_stats.new_members)}

🔄 Статус аккаунта:
• Всего добавлено: {status['total_added']}/50
• Осталось добавлений: {status['remaining_capacity']}
• За последние 24ч: {status['last_24h_adds']}

⏳ Следующее добавление через:
{status['time_remaining']['hours']}ч {status['time_remaining']['minutes']}м {status['time_remaining']['seconds']}с

❌ Ошибки добавления:
{chr(10).join(addition_result.failed_users[:5])}
{f'...и еще {len(addition_result.failed_users) - 5}' if len(addition_result.failed_users) > 5 else ''}

📨 Отправлены приглашения в ЛС:
{chr(10).join(addition_result.dm_sent[:5])}
{f'...и еще {len(addition_result.dm_sent) - 5}' if len(addition_result.dm_sent) > 5 else ''}
"""
            await send_result(chat_id, report)

            if batch_num < len(batches):
                await send_result(chat_id, f"⏳ Пауза {ACCOUNT_SETTINGS['delay_between_adds']} секунд...")
                await asyncio.sleep(ACCOUNT_SETTINGS['delay_between_adds'])

        return total_added

    except Exception as e:
        error_message = f"❌ Ошибка при работе с аккаунтом {phone}: {str(e)}"
        await send_result(chat_id, error_message)
        return 0


async def check_remaining_users(client, target_entity):
    """Проверяет, остались ли пользователи для добавления"""
    try:
        source_participants = await client.get_participants(target_entity, limit=1)
        return bool(source_participants)
    except Exception:
        return False




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


async def get_channel_participants_data(channel_username, chat_id, account):
    try:
        client = await get_or_create_client(account)
        channel = await client.get_entity(channel_username)

        await send_result(chat_id, "🔄 Получение данных об участниках...")

        # Получаем участников с дополнительной информацией
        participants = await client.get_participants(
            channel,
            limit=50,
            aggressive=True  # Получаем максимум доступной информации
        )

        info_chunks = []
        current_chunk = f"""
👥 Данные участников канала {channel.title}
📊 Всего получено: {len(participants)}
──────────────────
"""

        for p in participants:
            # Определяем статус пользователя
            status = "Онлайн" if getattr(p.status, 'online', False) else "Оффлайн"
            last_seen = getattr(p.status, 'was_online', 'Неизвестно')

            # Проверяем, является ли пользователь ботом или премиум
            is_bot = "Да" if p.bot else "Нет"
            is_premium = "Да" if getattr(p, 'premium', False) else "Нет"

            user_info = f"""
👤 Пользователь:
• ID: {p.id}
• Имя: {p.first_name or 'Не указано'}
• Фамилия: {p.last_name or 'Не указано'}
• Username: @{p.username or 'Отсутствует'}
• Телефон: {'+' + str(p.phone) if p.phone else 'Скрыт'}

📱 Статус:
• Активность: {status}
• Последний визит: {last_seen}
• Бот: {is_bot}
• Premium: {is_premium}

🔒 Приватность:
• Фото профиля: {'Доступно' if p.photo else 'Отсутствует/Скрыто'}
• Verified: {'Да' if p.verified else 'Нет'}
• Ограничен: {'Да' if p.restricted else 'Нет'}
──────────────────
"""
            # Если текущий чанк станет слишком большим, начинаем новый
            if len(current_chunk) + len(user_info) > 4000:
                info_chunks.append(current_chunk)
                current_chunk = user_info
            else:
                current_chunk += user_info

        # Добавляем последний чанк
        if current_chunk:
            info_chunks.append(current_chunk)

        # Добавляем статистику в первый чанк
        bots_count = sum(1 for p in participants if p.bot)
        premium_count = sum(1 for p in participants if getattr(p, 'premium', False))
        with_username = sum(1 for p in participants if p.username)

        stats = f"""
📊 Статистика участников:
• Всего проверено: {len(participants)}
• С username: {with_username} ({(with_username / len(participants) * 100):.1f}%)
• Ботов: {bots_count} ({(bots_count / len(participants) * 100):.1f}%)
• Premium: {premium_count} ({(premium_count / len(participants) * 100):.1f}%)
──────────────────

"""
        info_chunks[0] = stats + info_chunks[0]

        # Отправляем чанки с прогресс-баром
        total_chunks = len(info_chunks)
        for i, chunk in enumerate(info_chunks, 1):
            progress = f"[{i}/{total_chunks}] "
            await send_result(chat_id, progress + chunk)
            await asyncio.sleep(1)  # Пауза между отправкой чанков

        # Отправляем итоговую статистику
        summary = f"""
✅ Сбор данных завершен!
📊 Итоги:
• Обработано участников: {len(participants)}
• Отправлено сообщений: {len(info_chunks)}
• Размер данных: {sum(len(chunk) for chunk in info_chunks)} символов
"""
        await send_result(chat_id, summary)

    except Exception as e:
        error_message = f"""
❌ Ошибка при получении данных:
• Тип ошибки: {type(e).__name__}
• Описание: {str(e)}

💡 Возможные причины:
• Недостаточно прав в канале
• Канал не существует
• Ограничения приватности
"""
        await send_result(chat_id, error_message)


async def monitor_command_file():
    auto_resume_tasks = {}  # Хранение задач автовозобновления

    async def schedule_auto_resume(source_channel, target_channel, chat_id):
        while True:
            try:
                current_time = datetime.datetime.now()

                # Проверяем наличие пользователей для добавления
                client = await get_or_create_client(ACCOUNTS[0])
                source_entity = await client.get_entity(source_channel)
                source_participants = await get_valid_participants(client, source_entity, limit=1)

                if not source_participants:
                    await send_result(chat_id, """
✅ Все доступные пользователи добавлены!
📊 Автоматическое добавление остановлено
""")
                    return

                # Проверяем доступные аккаунты
                available_accounts = []
                next_available_time = None

                for account in ACCOUNTS:
                    status = tracker.get_account_status(account['phone'])
                    if status['remaining_capacity'] > 0:
                        available_accounts.append(account)
                    elif status['time_remaining']['hours'] > 0:
                        if next_available_time is None or status['time_remaining']['hours'] < next_available_time:
                            next_available_time = status['time_remaining']['hours']

                if available_accounts:
                    await send_result(chat_id, f"""
🔄 Автоматическое возобновление добавления
• Доступно аккаунтов: {len(available_accounts)}/{len(ACCOUNTS)}
• Канал-источник: {source_channel}
• Целевой канал: {target_channel}
• Осталось пользователей: {len(await get_valid_participants(client, source_entity))}
""")

                    command_data = {
                        "command": "add_user_to_channel",
                        "source_channel": source_channel,
                        "target_channel": target_channel,
                        "chat_id": chat_id,
                        "accounts": [acc['phone'] for acc in available_accounts]
                    }

                    with open(command_file, 'w') as f:
                        json.dump(command_data, f)
                else:
                    if next_available_time:
                        await send_result(chat_id, f"""
⏳ Все аккаунты на паузе
• Следующий аккаунт будет доступен через: {next_available_time}ч
• Автоматическое продолжение после паузы
""")

                await asyncio.sleep(12 * 3600)  # Ждем 12 часов

            except Exception as e:
                print(f"Ошибка в автовозобновлении: {str(e)}")
                await asyncio.sleep(300)  # Пауза 5 минут при ошибке

    # Основной цикл мониторинга
    while True:
        try:
            if os.path.exists(command_file) and os.path.getsize(command_file) > 0:
                with open(command_file, 'r') as file:
                    command_data = json.load(file)

                if command_data.get('command') == "add_user_to_channel":
                    total_added = 0
                    successful_accounts = 0
                    failed_accounts = []
                    accounts = [acc for acc in ACCOUNTS if acc['phone'] in command_data.get('accounts', [])]

                    # Получаем начальное состояние канала
                    client = await get_or_create_client(accounts[0])
                    target_entity = await client.get_entity(command_data['target_channel'])
                    initial_members = await client.get_participants(target_entity, limit=0)
                    initial_count = len(initial_members)

                    # Проверяем доступные аккаунты
                    available_accounts = []
                    for account in accounts:
                        status = tracker.get_account_status(account['phone'])
                        if status['remaining_capacity'] > 0:
                            available_accounts.append(account)
                        else:
                            time_remaining = status['time_remaining']
                            failed_accounts.append({
                                'phone': account['phone'],
                                'reason': f"Лимит исчерпан. Доступен через {time_remaining['hours']}ч {time_remaining['minutes']}м"
                            })

                    if not available_accounts:
                        next_available = min(
                            (acc for acc in failed_accounts),
                            key=lambda x: int(x['reason'].split('через ')[1].split('ч')[0])
                        )

                        await send_result(command_data['chat_id'], f"""
❌ Нет доступных аккаунтов!

📱 Статус аккаунтов:
{chr(10).join(f"• {acc['phone']}: {acc['reason']}" for acc in failed_accounts)}

⏳ Ближайший доступный аккаунт:
• {next_available['phone']}
• {next_available['reason']}
""")

                        # Запускаем автовозобновление
                        channel_key = f"{command_data['source_channel']}_{command_data['target_channel']}"
                        if channel_key not in auto_resume_tasks:
                            task = asyncio.create_task(schedule_auto_resume(
                                command_data['source_channel'],
                                command_data['target_channel'],
                                command_data['chat_id']
                            ))
                            auto_resume_tasks[channel_key] = task

                            await send_result(command_data['chat_id'], """
✅ Автоматическое возобновление активировано
• Система продолжит добавление через 12 часов
• Будут использоваться все доступные аккаунты
• Для остановки используйте команду /stop
""")
                        continue

                    # Работаем с доступными аккаунтами
                    await send_result(command_data['chat_id'], f"""
🚀 Начинаем процесс инвайтинга
• Доступно аккаунтов: {len(available_accounts)}/{len(accounts)}
• Канал-источник: {command_data['source_channel']}
• Целевой канал: {command_data['target_channel']}
• Текущее количество участников: {initial_count}
""")

                    for i, account in enumerate(available_accounts):
                        try:
                            account_status = tracker.get_account_status(account['phone'])

                            # Проверяем количество участников перед добавлением
                            pre_add_count = len(await client.get_participants(target_entity, limit=0))

                            await send_result(command_data['chat_id'], f"""
                    📱 Работаем с аккаунтом: {account['phone']}
                    • Осталось добавлений: {account_status['remaining_capacity']}
                    • За последние 24ч: {account_status['last_24h_adds']}
                    • Текущее количество участников: {pre_add_count}
                    """)

                            added = await add_user_to_channel(
                                account=account,
                                source_channel=command_data['source_channel'],
                                target_channel=command_data['target_channel'],
                                chat_id=command_data['chat_id']
                            )

                            # Проверяем фактическое количество добавленных
                            post_add_count = len(await client.get_participants(target_entity, limit=0))
                            actual_added = post_add_count - pre_add_count

                            if actual_added > 0:
                                total_added += actual_added
                                successful_accounts += 1
                                await send_result(command_data['chat_id'], f"""
                    📊 Результат добавления:
                    • Фактически добавлено: {actual_added}
                    • Всего в канале: {post_add_count}
                    """)
                            else:
                                failed_accounts.append({
                                    'phone': account['phone'],
                                    'reason': "Не удалось добавить пользователей"
                                })

                            if i < len(available_accounts) - 1:
                                next_account = available_accounts[i + 1]
                                next_status = tracker.get_account_status(next_account['phone'])
                                await send_result(command_data['chat_id'], f"""
                    ⏳ Переключение аккаунта...
                    📱 Следующий: {next_account['phone']}
                    📊 Доступно добавлений: {next_status['remaining_capacity']}
                    ⏰ Пауза {ACCOUNT_SETTINGS['delay_between_accounts']} секунд...
                    """)
                                await asyncio.sleep(ACCOUNT_SETTINGS['delay_between_accounts'])

                        except Exception as e:
                            print(f"Ошибка в аккаунте {account['phone']}: {str(e)}")
                            failed_accounts.append({
                                'phone': account['phone'],
                                'reason': f"Ошибка: {str(e)}"
                            })
                            continue

                        # Финальная проверка результатов
                    final_count = len(await client.get_participants(target_entity, limit=0))
                    total_added_verified = final_count - initial_count

                    # Формируем итоговый отчет
                    overall_stats = tracker.get_overall_stats()
                    summary = f"""
                    {'✅' if successful_accounts > 0 else '⚠️'} Процесс завершен!

                    📊 Результаты работы:
                    • Было участников: {initial_count}
                    • Стало участников: {final_count}
                    • Фактически добавлено: {total_added_verified}
                    • Успешных аккаунтов: {successful_accounts}/{len(accounts)}
                    • За 24 часа всего: {overall_stats['total_added_24h']}
                    • За всё время: {overall_stats['total_added_all_time']}

                    📱 Статус аккаунтов:
                    {chr(10).join(f"• {acc['phone']}: {acc['reason']}" for acc in failed_accounts)} 

                    ⚠️ Следующий запуск:
                    • Доступно аккаунтов: {overall_stats['accounts_available']}/{len(ACCOUNTS)}
                    • Каждый аккаунт может добавить по 50 пользователей
                    • Новый цикл через 12 часов после последнего использования каждого аккаунта
                    """
                    await send_result(command_data['chat_id'], summary)

                    # Проверяем остались ли пользователи для добавления
                    source_entity = await client.get_entity(command_data['source_channel'])
                    remaining_users = len(await get_valid_participants(client, source_entity))

                    if remaining_users > 0:
                        # Запускаем автовозобновление
                        channel_key = f"{command_data['source_channel']}_{command_data['target_channel']}"
                        if channel_key not in auto_resume_tasks:
                            task = asyncio.create_task(schedule_auto_resume(
                                command_data['source_channel'],
                                command_data['target_channel'],
                                command_data['chat_id']
                            ))
                            auto_resume_tasks[channel_key] = task

                            await send_result(command_data['chat_id'], f"""
                    🔄 Автоматическое добавление активировано
                    • Осталось добавить: {remaining_users} пользователей
                    • Следующий запуск через 12 часов
                    • Для остановки используйте /stop
                    """)

                elif command_data.get('command') == "stop_auto_resume":
                    channel_key = f"{command_data['source_channel']}_{command_data['target_channel']}"
                    if channel_key in auto_resume_tasks:
                        auto_resume_tasks[channel_key].cancel()
                        del auto_resume_tasks[channel_key]
                        await send_result(command_data['chat_id'], """
                    ⏹ Автоматическое добавление остановлено
                    • Для нового добавления используйте /add
                    """)

                elif command_data.get('command') == "get_channel_info":
                    await get_channel_info(
                        command_data['channel'],
                        command_data['chat_id'],
                        command_data['account']
                    )

                elif command_data.get('command') == "get_channel_participants_data":
                    await get_channel_participants_data(
                        command_data['channel'],
                        command_data['chat_id'],
                        command_data['account']
                    )

                open(command_file, 'w').close()

                await asyncio.sleep(1)

        except Exception as e:
            error_message = f"""
                    ❌ Ошибка при обработке команды:
                    • Тип ошибки: {type(e).__name__}
                    • Описание: {str(e)}

                    🔄 Попробуйте повторить операцию позже
                    """
            print(error_message)
            try:
                await send_result(command_data['chat_id'], error_message)
            except:
                pass
            await asyncio.sleep(5)


async def main():
    print("✅ Telethon процесс запущен")
    await monitor_command_file()


if __name__ == "__main__":
    asyncio.run(main())
