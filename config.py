# config.py

# Список всех прокси
PROXIES = [
    {
        'scheme': 'socks5',
        'hostname': '46.232.13.72',
        'port': 8000,
        'username': 'e4mdv3',
        'password': 'fbpkSr'
    },
    {
        'scheme': 'socks5',
        'hostname': '45.140.249.190',
        'port': 8000,
        'username': 'gsyRkx',
        'password': 'qxnrk5'
    },
    {
        'scheme': 'socks5',
        'hostname': '147.45.85.237',
        'port': 8000,
        'username': 'WPaPmC',
        'password': '9xw6aM'
    },
    {
        'scheme': 'socks5',
        'hostname': '46.232.13.127',
        'port': 8000,
        'username': 'SVxTsX',
        'password': 'qD34zG'
    },
    {
        'scheme': 'socks5',
        'hostname': '46.232.15.22',
        'port': 8000,
        'username': 'SVxTsX',
        'password': 'qD34zG'
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.202.160',
        'port': 8000,
        'username': 'P03BsX',
        'password': 'CZGUDh'
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.201.37',
        'port': 8000,
        'username': 'P03BsX',
        'password': 'CZGUDh'
    },
    {
        'scheme': 'socks5',
        'hostname': '168.80.83.127',
        'port': 8000,
        'username': '0FEcWZ',
        'password': 'SxUfKU'
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
        'proxy': PROXIES[0]  # Первый прокси
    },
    {
        'phone': '+996555959260',
        'api_id': '17487098',
        'api_hash': '065f601d7ca35a1cda718b53ba926727',
        'proxy': PROXIES[1]  # Второй прокси
    },
    {
        'phone': '+996555950567',
        'api_id': '25778445',
        'api_hash': 'e95907153ce835dc6d9a77419cf450e8',
        'proxy': PROXIES[2]  # Третий прокси
    },
    {
        'phone': '+996555959258',
        'api_id': '27987795',
        'api_hash': '58c8976d674b2be56621ac1c42361de7',
        'proxy': PROXIES[3]  # Четвертый прокси
    },
    {
        'phone': '+996555651684',
        'api_id': '24596112',
        'api_hash': '68b2948c90783861e50e203137532561',
        'proxy': PROXIES[4]  # Пятый прокси
    },
    {
        'phone': '+996555950617',
        'api_id': '22028301',
        'api_hash': '28c83f7f15a83f76894939b62959b7eb',
        'proxy': PROXIES[5]  # Шестой прокси
    },
    {
        'phone': '+996555959986',
        'api_id': '26917899',
        'api_hash': '1a89da6685f7bb78a98146d33e7cccb2',
        'proxy': PROXIES[6]  # Седьмой прокси
    },
    {
        'phone': '+996555959984',
        'api_id': '21995504',
        'api_hash': '501e8e2b1603ec476dc60703253a650b',
        'proxy': PROXIES[7]  # Восьмой прокси
    }
]

# Обновленные настройки для работы с аккаунтами
ACCOUNT_SETTINGS = {
    'batch_size': 25,           # Размер группы для добавления (25 пользователей за раз)
    'invites_per_run': 2,       # Количество запусков до перерыва (2 раза по 25)
    'max_retries': 3,           # Максимальное количество попыток при ошибке
    'delay_between_adds': 20,  # Пауза между добавлениями групп (3 минуты)
    'delay_between_accounts': 10,  # Пауза между аккаунтами (5 минут)
    'cooldown_hours': 12,       # Время перерыва между циклами (12 часов)
    'users_per_account': 50,    # Общее количество пользователей на аккаунт (25 × 2)
    'min_delay': 10,           # Минимальная пауза между действиями (1 минута)
    'max_delay': 90,         # Максимальная пауза между действиями (2 минуты)
    'privacy_check_delay': 2,  # Задержка между проверками приватности
    'user_add_delay': 3      # Задержка между добавлениями отдельных пользователей
}

# Статусы для отслеживания прогресса
INVITE_STAGES = {
    'FIRST_BATCH': 'Добавление первой группы (25 пользователей)',
    'SECOND_BATCH': 'Добавление второй группы (25 пользователей)',
    'COOLDOWN': 'Перерыв 12 часов'
}

INVITE_SETTINGS = {
    'max_retries': 3,
    'min_batch_size': 25,
    'total_users_needed': 50,
    'check_existing': True,
    'shuffle_users': True,
    'verbose_logging': True
}

