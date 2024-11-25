import warnings
warnings.filterwarnings('ignore')

import telebot
import json
import threading
from time import sleep
import os
import hashlib
import random
from collections import defaultdict
import datetime
from config import ACCOUNTS, PROXIES, BOT_TOKEN, ADMIN_USERNAME, ADMIN_PASSWORD, ACCOUNT_SETTINGS


bot = telebot.TeleBot(BOT_TOKEN)
command_file = 'command.json'
result_file = 'result.json'


# Хранилище состояний
authorized_users = {}
auth_states = {}
channel_states = {}
account_status = defaultdict(lambda: {'last_used': None, 'users_added': 0})


def hash_credentials(text):
    return hashlib.sha256(text.encode()).hexdigest()


def get_next_available_account():
    current_time = datetime.datetime.now()

    for account in ACCOUNTS:
        last_used = account_status[account['phone']]['last_used']
        users_added = account_status[account['phone']]['users_added']

        if last_used is None or (current_time - last_used).total_seconds() >= 12 * 3600:
            if users_added < 50:
                return account
            elif (current_time - last_used).total_seconds() >= 24 * 3600:
                account_status[account['phone']]['users_added'] = 0
                return account

    return None


def get_account_status_emoji(account):
    current_time = datetime.datetime.now()
    last_used = account_status[account['phone']]['last_used']
    users_added = account_status[account['phone']]['users_added']

    if last_used is None:
        return "✅"

    hours_passed = (current_time - last_used).total_seconds() / 3600
    if hours_passed >= 24:
        return "✅"
    elif hours_passed >= 12 and users_added < 50:
        return "✅"
    else:
        return "⏳"


def require_auth(func):
    def wrapper(message, *args, **kwargs):
        if message.chat.id not in authorized_users or not authorized_users[message.chat.id]:
            bot.reply_to(message, "⛔ Необходима авторизация. Используйте /login для входа.")
            return
        return func(message, *args, **kwargs)

    return wrapper


@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.id in authorized_users and authorized_users[message.chat.id]:
        bot.reply_to(message, "Вы уже авторизованы. Используйте /help для списка команд.")
    else:
        bot.reply_to(message,
                     "👋 Добро пожаловать! Для начала работы необходимо авторизоваться.\nИспользуйте /login для входа.")


@bot.message_handler(commands=['login'])
def login_command(message):
    if message.chat.id in authorized_users and authorized_users[message.chat.id]:
        bot.reply_to(message, "Вы уже авторизованы!")
        return

    auth_states[message.chat.id] = {'state': 'waiting_username'}
    bot.reply_to(message, "👤 Введите логин:")


@bot.message_handler(commands=['logout'])
@require_auth
def logout_command(message):
    authorized_users[message.chat.id] = False
    if message.chat.id in auth_states:
        del auth_states[message.chat.id]
    if message.chat.id in channel_states:
        del channel_states[message.chat.id]
    bot.reply_to(message, "👋 Вы успешно вышли из системы!")


@bot.message_handler(commands=['status'])
@require_auth
def status_command(message):
    current_time = datetime.datetime.now()
    status_message = "📱 Статус аккаунтов:\n\n"

    for account in ACCOUNTS:
        phone = account['phone']
        status = account_status[phone]
        last_used = status['last_used']
        users_added = status['users_added']
        emoji = get_account_status_emoji(account)

        status_message += f"{emoji} Аккаунт: {phone}\n"
        status_message += f"└ Добавлено: {users_added}/{ACCOUNT_SETTINGS['users_per_account']} пользователей\n"

        if last_used:
            next_available = last_used + datetime.timedelta(hours=ACCOUNT_SETTINGS['cooldown_hours'])
            if current_time >= next_available:
                status_message += f"└ Доступен сейчас\n"
            else:
                time_remaining = next_available - current_time
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                status_message += f"└ Будет доступен через: {hours}ч {minutes}мин\n"
        else:
            status_message += f"└ Доступен сейчас\n"

        status_message += "\n"

    # Добавляем общую статистику
    total_users_added = sum(account_status[acc['phone']]['users_added'] for acc in ACCOUNTS)
    total_capacity = len(ACCOUNTS) * ACCOUNT_SETTINGS['users_per_account']

    status_message += f"""
📊 Общая статистика:
• Всего добавлено: {total_users_added}/{total_capacity}
• Размер группы: {ACCOUNT_SETTINGS['batch_size']}
• Добавлений на аккаунт: {ACCOUNT_SETTINGS['invites_per_run']}
• Перерыв: {ACCOUNT_SETTINGS['cooldown_hours']} часов
"""

    bot.reply_to(message, status_message)


@bot.message_handler(commands=['help'])
@require_auth
def help_command(message):
    help_text = """
📚 Доступные команды:

/status - Проверить статус всех аккаунтов
/add - Добавить пользователей в канал
/get_channel_info - Получить информацию о канале
/get_channel_participants_data - Получить данные об участниках
/logout - Выйти из системы

⚠️ Важные ограничения:
• Каждый аккаунт может добавить до 50 пользователей
• После использования требуется пауза 12 часов
• Работает только с пользователями, у которых есть username
"""
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['get_channel_info'])
@require_auth
def get_channel_info_command(message):
    msg = bot.reply_to(message, "📝 Введите username или ID канала для анализа (например, @example):")
    bot.register_next_step_handler(msg, process_channel_info)


@require_auth
def process_channel_info(message):
    channel_username = message.text.strip()
    if channel_username:
        command_data = {
            "command": "get_channel_info",
            "channel": channel_username,
            "chat_id": message.chat.id,
            "account": ACCOUNTS[0]  # Используем первый аккаунт для получения информации
        }
        with open(command_file, 'w') as file:
            json.dump(command_data, file)
        bot.reply_to(message, "⏳ Запрос на получение информации о канале отправлен. Ожидайте результата...")
    else:
        bot.reply_to(message, "❌ Пожалуйста, введите корректный username или ID канала.")


@bot.message_handler(commands=['get_channel_participants_data'])
@require_auth
def get_participants_command(message):
    msg = bot.reply_to(message, "📝 Введите username или ID канала:")
    bot.register_next_step_handler(msg, process_participants_request)


@require_auth
def process_participants_request(message):
    channel_username = message.text.strip()
    if channel_username:
        command_data = {
            "command": "get_channel_participants_data",
            "channel": channel_username,
            "chat_id": message.chat.id,
            "account": ACCOUNTS[0]  # Используем первый аккаунт для получения данных
        }
        with open(command_file, 'w') as file:
            json.dump(command_data, file)
        bot.reply_to(message, "⏳ Запрос на получение данных участников отправлен. Ожидайте результата...")
    else:
        bot.reply_to(message, "❌ Пожалуйста, введите корректный username или ID канала.")


@bot.message_handler(func=lambda message: message.chat.id in auth_states)
def handle_auth(message):
    chat_id = message.chat.id
    state = auth_states.get(chat_id, {}).get('state')

    if state == 'waiting_username':
        if hash_credentials(message.text) == hash_credentials(ADMIN_USERNAME):
            auth_states[chat_id] = {'state': 'waiting_password', 'username': message.text}
            bot.reply_to(message, "🔑 Введите пароль:")
        else:
            del auth_states[chat_id]
            bot.reply_to(message, "❌ Неверный логин. Попробуйте /login снова.")

    elif state == 'waiting_password':
        if hash_credentials(message.text) == hash_credentials(ADMIN_PASSWORD):
            authorized_users[chat_id] = True
            del auth_states[chat_id]
            bot.reply_to(message, """
✅ Авторизация успешна!

Доступные команды:
/status - Проверить статус всех аккаунтов
/add - Добавить пользователей в канал
/get_channel_info - Получить информацию о канале
/get_channel_participants_data - Получить данные об участниках
/help - Показать все команды
/logout - Выйти из системы
""")
        else:
            del auth_states[chat_id]
            bot.reply_to(message, "❌ Неверный пароль. Попробуйте /login снова.")


@bot.message_handler(commands=['add'])
@require_auth
def add_command(message):
    available_accounts = []
    current_time = datetime.datetime.now()

    # Проверяем все доступные аккаунты
    for account in ACCOUNTS:
        last_used = account_status[account['phone']]['last_used']
        users_added = account_status[account['phone']]['users_added']

        if (last_used is None or
                (current_time - last_used).total_seconds() >= ACCOUNT_SETTINGS['cooldown_hours'] * 3600):
            if users_added < ACCOUNT_SETTINGS['users_per_account']:
                available_accounts.append(account)
            elif (current_time - last_used).total_seconds() >= 24 * 3600:
                account_status[account['phone']]['users_added'] = 0
                available_accounts.append(account)

    if not available_accounts:
        # Находим время до следующего доступного аккаунта
        next_available_time = min(
            (account_status[acc['phone']]['last_used'] +
             datetime.timedelta(hours=ACCOUNT_SETTINGS['cooldown_hours']))
            for acc in ACCOUNTS
            if account_status[acc['phone']]['last_used'] is not None
        )

        time_remaining = next_available_time - current_time
        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)

        wait_message = f"""
⚠️ Сейчас нет доступных аккаунтов
ℹ️ Все аккаунты на перерыве после добавления {ACCOUNT_SETTINGS['users_per_account']} пользователей

⏰ Следующий аккаунт будет доступен через:
{hours}ч {minutes}мин
"""
        bot.reply_to(message, wait_message)
        return

    channel_states[message.chat.id] = {
        'state': 'waiting_source',
        'accounts': available_accounts
    }

    bot.reply_to(message, f"""
📥 Введите username канала ОТКУДА брать пользователей
Например: @channel

ℹ️ Доступно аккаунтов: {len(available_accounts)}/{len(ACCOUNTS)}
📊 План добавления:
• {ACCOUNT_SETTINGS['batch_size']} пользователей за раз
• {ACCOUNT_SETTINGS['invites_per_run']} раза подряд
• Всего {ACCOUNT_SETTINGS['users_per_account']} пользователей с аккаунта
• {len(available_accounts) * ACCOUNT_SETTINGS['users_per_account']} пользователей со всех аккаунтов
⏳ Перерыв между группами: {ACCOUNT_SETTINGS['delay_between_adds']} секунд
🕒 Перерыв между аккаунтами: {ACCOUNT_SETTINGS['delay_between_accounts']} секунд
""")


@bot.message_handler(func=lambda message:
message.chat.id in channel_states and
channel_states[message.chat.id].get('state') in ['waiting_source', 'waiting_target'])
@require_auth
def handle_channel_input(message):
    chat_id = message.chat.id
    state = channel_states[chat_id]['state']
    available_accounts = channel_states[chat_id]['accounts']

    if state == 'waiting_source':
        source_channel = message.text.strip()
        if not source_channel.startswith('@'):
            bot.reply_to(message, "❌ Username должен начинаться с @")
            return

        channel_states[chat_id].update({
            'state': 'waiting_target',
            'source_channel': source_channel
        })
        bot.reply_to(message, "📤 Теперь введите username канала КУДА добавлять пользователей\nНапример: @channel")

    elif state == 'waiting_target':
        target_channel = message.text.strip()
        if not target_channel.startswith('@'):
            bot.reply_to(message, "❌ Username должен начинаться с @")
            return

        command_data = {
            'command': 'add_user_to_channel',
            'source_channel': channel_states[chat_id]['source_channel'],
            'target_channel': target_channel,
            'chat_id': chat_id,
            'accounts': [acc['phone'] for acc in available_accounts],
            'batch_size': ACCOUNT_SETTINGS['batch_size'],
            'invites_per_run': ACCOUNT_SETTINGS['invites_per_run'],
            'delay_between_adds': ACCOUNT_SETTINGS['delay_between_adds'],
            'delay_between_accounts': ACCOUNT_SETTINGS['delay_between_accounts']
        }

        # Сохранение команды в файл для дальнейшей обработки
        with open(command_file, 'w') as file:
            json.dump(command_data, file)

        bot.reply_to(message, f"""
        ✅ Задача добавления пользователей создана!
        📥 Источник: {channel_states[chat_id]['source_channel']}
        📤 Цель: {target_channel}
        ⏳ Обработка начнётся в ближайшее время. Ожидайте уведомления!
                """)

        # Сбрасываем состояние пользователя
        del channel_states[chat_id]
def check_for_results():
    while True:
        try:
            if os.path.exists(result_file):
                with open(result_file, 'r') as file:
                    result = json.load(file)
                    if 'chat_id' in result and 'data' in result:
                        bot.send_message(result['chat_id'], result['data'])
                        open(result_file, 'w').close()
        except Exception as e:
            print(f"Ошибка при проверке результатов: {e}")
        sleep(5)

# Запускаем поток проверки результатов
result_thread = threading.Thread(target=check_for_results, daemon=True)
result_thread.start()

if __name__ == "__main__":
    print("Telebot запущен")
    bot.polling(none_stop=True)
