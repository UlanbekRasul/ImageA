# config.py

from typing import Dict, List
import os

# Базовые настройки бота
BOT_SETTINGS = {
    'TOKEN': '7639398186:AAGDC_FAXoxnLnSpNjMuGKFHHEfoutSzhpg',
    'ADMIN_USERNAME': "admin",
    'ADMIN_PASSWORD': "admin",
    'MAX_MESSAGE_LENGTH': 4096,
    'COMMAND_COOLDOWN': 3,  # Задержка между командами в секундах
    'ERROR_RETRY_DELAY': 5  # Задержка при ошибках в секундах
}

# Настройки прокси с проверкой доступности
PROXY_SETTINGS = {
    'TIMEOUT': 10,  # Таймаут подключения
    'CHECK_INTERVAL': 300,  # Интервал проверки прокси (5 минут)
    'AUTO_ROTATE': True,  # Автоматическая ротация при ошибках
    'MAX_FAILURES': 3  # Максимальное количество ошибок до смены прокси
}

# Список всех прокси
PROXIES: List[Dict] = [
    {
        'scheme': 'socks5',
        'hostname': '46.232.13.72',
        'port': 8000,
        'username': 'e4mdv3',
        'password': 'fbpkSr',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True
    },
    {
        'scheme': 'socks5',
        'hostname': '45.140.249.190',
        'port': 8000,
        'username': 'gsyRkx',
        'password': 'qxnrk5',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '147.45.85.237',
        'port': 8000,
        'username': 'WPaPmC',
        'password': '9xw6aM',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '46.232.13.127',
        'port': 8000,
        'username': 'SVxTsX',
        'password': 'qD34zG',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '46.232.15.22',
        'port': 8000,
        'username': 'SVxTsX',
        'password': 'qD34zG',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.202.160',
        'port': 8000,
        'username': 'P03BsX',
        'password': 'CZGUDh',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.201.37',
        'port': 8000,
        'username': 'P03BsX',
        'password': 'CZGUDh',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.83.127',
        'port': 8000,
        'username': '0FEcWZ',
        'password': 'SxUfKU',
        'failures': 0,  # Счетчик ошибок
        'last_used': None,  # Время последнего использования
        'is_available': True  # Флаг доступности
    }
]

# Настройки бота
BOT_TOKEN = '7639398186:AAGDC_FAXoxnLnSpNjMuGKFHHEfoutSzhpg'
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Конфигурация аккаунтов с привязкой к прокси
ACCOUNTS = [
    {
        'phone': '+996507400600',
        'api_id': '26450187',
        'api_hash': '93774e7809dfd98c006c9fba966321a8',
        'proxy': PROXIES[0],
        'device_model': 'Samsung Galaxy S21',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555959260',
        'api_id': '17487098',
        'api_hash': '065f601d7ca35a1cda718b53ba926727',
        'proxy': PROXIES[1],
        'device_model': 'Samsung Galaxy S23',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555950567',
        'api_id': '25778445',
        'api_hash': 'e95907153ce835dc6d9a77419cf450e8',
        'proxy': PROXIES[2],
        'device_model': 'Samsung Galaxy S22',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555959258',
        'api_id': '27987795',
        'api_hash': '58c8976d674b2be56621ac1c42361de7',
        'proxy': PROXIES[3],
        'device_model': 'Samsung Galaxy S23 Ultra',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555651684',
        'api_id': '24596112',
        'api_hash': '68b2948c90783861e50e203137532561',
        'proxy': PROXIES[4],
        'device_model': 'Samsung Galaxy S21 Ultra',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555950617',
        'api_id': '22028301',
        'api_hash': '28c83f7f15a83f76894939b62959b7eb',
        'proxy': PROXIES[5],
        'device_model': 'Samsung Galaxy S20',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555959986',
        'api_id': '26917899',
        'api_hash': '1a89da6685f7bb78a98146d33e7cccb2',
        'proxy': PROXIES[6],
        'device_model': 'Samsung Galaxy S23 FE',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    },
    {
        'phone': '+996555959984',
        'api_id': '21995504',
        'api_hash': '501e8e2b1603ec476dc60703253a650b',
        'proxy': PROXIES[7],
        'device_model': 'Samsung Galaxy S22',  # Модель устройства
        'system_version': 'Android 12.0',  # Версия системы
        'app_version': '10.0.0',  # Версия приложения
        'lang_code': 'en',  # Язык
        'system_lang_code': 'en',  # Системный язык
        'status': {
            'active': True,  # Активен ли аккаунт
            'banned': False,  # Забанен ли
            'limited': False,  # Есть ли ограничения
            'verified': True  # Проверен ли
        }
    }
]

# Детальные настройки для аккаунтов
ACCOUNT_SETTINGS = {
    # Настройки групп
    'batch_size': 25,  # Размер группы для добавления
    'invites_per_run': 2,  # Количество запусков до перерыва

    # Временные интервалы
    'delay_between_adds': 20,  # Пауза между группами
    'delay_between_accounts': 10,  # Пауза между аккаунтами
    'cooldown_hours': 12,  # Время перерыва между циклами

    # Лимиты
    'users_per_account': 50,  # Пользователей на аккаунт
    'daily_limit': 100,  # Суточный лимит на аккаунт
    'max_retries': 3,  # Попытки при ошибках

    # Задержки
    'min_delay': 10,  # Минимальная пауза
    'max_delay': 90,  # Максимальная пауза
    'privacy_check_delay': 2,  # Задержка проверки приватности
    'user_add_delay': 3,  # Задержка между добавлениями

    # Дополнительные параметры
    'verify_additions': True,  # Проверять успешность добавления
    'collect_statistics': True,  # Собирать статистику
    'auto_retry_on_flood': True,  # Автоповтор при FloodWait
    'use_proxy_rotation': True  # Использовать ротацию прокси
}

# Настройки инвайтинга
INVITE_SETTINGS = {
    'max_retries': 3,
    'min_batch_size': 25,
    'total_users_needed': 50,
    'check_existing': True,
    'shuffle_users': True,
    'verbose_logging': True,
    'verify_membership': True,  # Проверять членство
    'skip_bots': True,  # Пропускать ботов
    'skip_deleted': True,  # Пропускать удаленных
    'save_progress': True  # Сохранять прогресс
}

# Статусы прогресса
INVITE_STAGES = {
    'FIRST_BATCH': 'Добавление первой группы (25 пользователей)',
    'SECOND_BATCH': 'Добавление второй группы (25 пользователей)',
    'COOLDOWN': 'Перерыв 12 часов'
}

# Пути к файлам
PATHS = {
    'SESSION_DIR': 'sessions',  # Директория для сессий
    'LOGS_DIR': 'logs',  # Директория для логов
    'STATS_DIR': 'statistics',  # Директория для статистики
    'TEMP_DIR': 'temp'  # Временная директория
}

# Создание необходимых директорий
for directory in PATHS.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

# Функции для работы с конфигом
def get_available_proxies() -> List[Dict]:
    """Возвращает список доступных прокси"""
    return [p for p in PROXIES if p['is_available']]

def get_account_by_phone(phone: str) -> Dict:
    """Возвращает информацию об аккаунте по номеру телефона"""
    return next((acc for acc in ACCOUNTS if acc['phone'] == phone), None)

def get_proxy_for_account(account: Dict) -> Dict:
    """Возвращает прокси для аккаунта"""
    return account.get('proxy')

def update_account_status(phone: str, status_update: Dict) -> None:
    """Обновляет статус аккаунта"""
    account = get_account_by_phone(phone)
    if account:
        account['status'].update(status_update)

# Проверка конфигурации
def verify_config() -> bool:
    """Проверяет корректность конфигурации"""
    try:
        assert len(PROXIES) >= len(ACCOUNTS), "Недостаточно прокси"
        assert all(acc.get('api_id') and acc.get('api_hash') for acc in ACCOUNTS), "Отсутствуют API credentials"
        assert BOT_SETTINGS['TOKEN'], "Отсутствует токен бота"
        assert ACCOUNT_SETTINGS['batch_size'] <= ACCOUNT_SETTINGS['users_per_account'], "Некорректный размер группы"
        return True
    except AssertionError as e:
        print(f"Ошибка конфигурации: {e}")
        return False

# Проверяем конфигурацию при импорте
if not verify_config():
    raise ValueError("Некорректная конфигурация")

