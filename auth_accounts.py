# auth_accounts.py

import asyncio
from telethon import TelegramClient
import os
import random
from config import ACCOUNTS, ACCOUNT_SETTINGS


async def auth_account(account, session_files):
    print(f"\n📱 Авторизация аккаунта {account['phone']}")

    proxy = account['proxy']
    print(f"""
🔄 Проверка подключения:
• Аккаунт: {account['phone']}
• Прокси: {proxy['hostname']}:{proxy['port']}
• Логин: {proxy['username']}
• Пароль: {proxy['password']}
""")

    device_model = f"Samsung Galaxy S{random.randint(20, 23)}"
    system_version = f"Android {random.randint(10, 13)}.0"
    session_file = f"session_{account['phone']}.session"

    try:
        client = TelegramClient(
            session_file,
            account['api_id'],
            account['api_hash'],
            device_model=device_model,
            system_version=system_version,
            proxy={
                'proxy_type': proxy['scheme'],
                'addr': proxy['hostname'],
                'port': proxy['port'],
                'username': proxy['username'],
                'password': proxy['password'],
                'rdns': True  # Добавляем для улучшения подключения
            }
        )

        print(f"🔄 Попытка подключения к Telegram через прокси...")
        await client.connect()

        if not await client.is_user_authorized():
            print(f"📱 Запрос кода авторизации...")
            try:
                await client.send_code_request(account['phone'])
                print(f"✅ Код отправлен на {account['phone']}")
            except Exception as e:
                print(f"❌ Ошибка отправки кода: {str(e)}")
                if "flood" in str(e).lower():
                    print("⚠️ Обнаружено ограничение на отправку кодов")
                    await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой
                return False

            code = input(f"📥 Введите код для {account['phone']}: ")
            await client.sign_in(account['phone'], code)
            print(f"✅ Аккаунт {account['phone']} авторизован")
            session_files.append(session_file)
            await asyncio.sleep(5)

        else:
            print(f"✅ Аккаунт {account['phone']} уже авторизован")
            session_files.append(session_file)

        await client.disconnect()
        return True

    except ConnectionError:
        print(f"❌ Ошибка подключения к прокси для {account['phone']}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


async def main():
    print(f"""
🔄 Начинаем процесс авторизации аккаунтов
📊 Общие настройки:
• Всего аккаунтов: {len(ACCOUNTS)}
• Размер группы: {ACCOUNT_SETTINGS['batch_size']}
• Добавлений на аккаунт: {ACCOUNT_SETTINGS['invites_per_run']}
• Пауза между группами: {ACCOUNT_SETTINGS['delay_between_adds']} сек
• Пауза между аккаунтами: {ACCOUNT_SETTINGS['delay_between_accounts']} сек
• Перерыв после работы: {ACCOUNT_SETTINGS['cooldown_hours']} часов
""")

    # Очистка старых сессий
    session_files = []
    for account in ACCOUNTS:
        session_file = f"session_{account['phone']}.session"
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"🗑 Удален старый файл сессии: {session_file}")

    successful = 0
    total = len(ACCOUNTS)

    for i, account in enumerate(ACCOUNTS, 1):
        print(f"\n👤 Обработка аккаунта {i}/{total}")
        try:
            if await auth_account(account, session_files):
                successful += 1
                print(f"✅ Аккаунт {i}/{total} успешно обработан")
            else:
                print(f"❌ Ошибка при обработке аккаунта {i}/{total}")

            if i < total:  # Пауза перед следующим аккаунтом
                await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ Непредвиденная ошибка для аккаунта {account['phone']}: {str(e)}")
            continue

    print(f"""
\n📊 Итоги авторизации:
✅ Успешно авторизовано: {successful}/{total} аккаунтов

🔄 Дальнейшие действия:
1. Запустите main.py для начала работы
2. Используйте команду /status для проверки состояния
3. Используйте команду /add для добавления пользователей
""")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Процесс прерван пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {str(e)}")
    finally:
        print("\n👋 Программа завершена")
