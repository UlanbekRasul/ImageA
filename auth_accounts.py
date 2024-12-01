# auth_accounts.py

import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneNumberBannedError
import os
import glob
import random
import json
from typing import List, Tuple, Dict
from config import ACCOUNTS, ACCOUNT_SETTINGS

# Файл для хранения статуса авторизации
AUTH_STATUS_FILE = 'auth_status.json'


class AuthResult:
    def __init__(self, phone: str):
        self.phone = phone
        self.success = False
        self.session_created = False
        self.error = None
        self.attempts = 0
        self.last_attempt = None


async def check_proxy(proxy: Dict) -> bool:
    """Проверяет работоспособность прокси"""
    try:
        client = TelegramClient(
            "proxy_check_session",
            api_id="1",
            api_hash="temp",
            proxy={
                'proxy_type': proxy['scheme'],
                'addr': proxy['hostname'],
                'port': proxy['port'],
                'username': proxy['username'],
                'password': proxy['password'],
                'rdns': True
            }
        )
        await client.connect()
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки прокси {proxy['hostname']}: {str(e)}")
        return False
    finally:
        if os.path.exists("proxy_check_session.session"):
            os.remove("proxy_check_session.session")

async def verify_account_access(client):
    """Проверка доступа аккаунта к API"""
    try:
        me = await client.get_me()
        return True
    except Exception:
        return False

def cleanup_sessions():
    """Очищает все старые сессии"""
    session_pattern = "session_*.session"
    cleaned = 0
    for session_file in glob.glob(session_pattern):
        try:
            os.remove(session_file)
            print(f"🗑 Удален файл сессии: {session_file}")
            cleaned += 1
        except Exception as e:
            print(f"❌ Ошибка при удалении {session_file}: {str(e)}")
    return cleaned


async def auth_account(account: Dict, result: AuthResult) -> bool:
    """Авторизует один аккаунт"""
    result.attempts += 1

    print(f"\n📱 Попытка авторизации аккаунта {account['phone']}")

    proxy = account['proxy']
    session_file = f"session_{account['phone']}.session"

    # Проверяем прокси
    if not await check_proxy(proxy):
        result.error = "Ошибка подключения к прокси"
        return False

    device_model = f"Samsung Galaxy S{random.randint(20, 23)}"
    system_version = f"Android {random.randint(10, 13)}.0"

    try:
        client = TelegramClient(
            session_file,
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

        print(f"🔄 Подключение через прокси {proxy['hostname']}...")
        await client.connect()

        if not await client.is_user_authorized():
            try:
                await client.send_code_request(account['phone'])
                print(f"✅ Код отправлен на {account['phone']}")

                code = input(f"📥 Введите код для {account['phone']}: ")
                await client.sign_in(account['phone'], code)

                print(f"✅ Аккаунт {account['phone']} авторизован")
                result.session_created = True

            except FloodWaitError as e:
                wait_time = e.seconds
                print(f"⚠️ Ожидание {wait_time} секунд перед следующей попыткой")
                await asyncio.sleep(wait_time)
                result.error = f"FloodWait: {wait_time} секунд"
                return False

            except Exception as e:
                print(f"❌ Ошибка авторизации: {str(e)}")
                result.error = str(e)
                return False

        else:
            print(f"✅ Аккаунт {account['phone']} уже авторизован")
            result.session_created = True

        await client.disconnect()
        result.success = True
        return True

    except PhoneNumberBannedError:
        result.error = "Аккаунт заблокирован"
        print(f"❌ Аккаунт {account['phone']} заблокирован")
        return False

    except Exception as e:
        result.error = str(e)
        print(f"❌ Ошибка: {str(e)}")
        return False


async def auth_accounts_batch(accounts: List[Dict], semaphore: asyncio.Semaphore) -> List[AuthResult]:
    """Авторизует группу аккаунтов параллельно"""
    results = [AuthResult(account['phone']) for account in accounts]

    async def auth_with_semaphore(account: Dict, result: AuthResult):
        async with semaphore:
            await auth_account(account, result)

    tasks = [
        asyncio.create_task(auth_with_semaphore(account, result))
        for account, result in zip(accounts, results)
    ]

    await asyncio.gather(*tasks)
    return results


async def save_auth_status(results: List[AuthResult]):
    """Сохраняет статус авторизации"""
    status = {
        result.phone: {
            'success': result.success,
            'session_created': result.session_created,
            'error': result.error,
            'attempts': result.attempts
        }
        for result in results
    }

    with open(AUTH_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


async def main():
    print(f"""
🚀 Запуск процесса авторизации аккаунтов
===========================================
📊 Настройки:
• Всего аккаунтов: {len(ACCOUNTS)}
• Параллельных авторизаций: 3
• Задержка между попытками: 5 секунд
""")

    # Очистка старых сессий
    cleaned = cleanup_sessions()
    print(f"🧹 Очищено сессий: {cleaned}")

    # Разбиваем аккаунты на группы по 3
    batch_size = 3
    account_batches = [ACCOUNTS[i:i + batch_size] for i in range(0, len(ACCOUNTS), batch_size)]

    # Семафор для ограничения параллельных подключений
    semaphore = asyncio.Semaphore(3)

    all_results = []

    for batch_num, batch in enumerate(account_batches, 1):
        print(f"\n📱 Обработка группы {batch_num}/{len(account_batches)}")

        results = await auth_accounts_batch(batch, semaphore)
        all_results.extend(results)

        successful = sum(1 for r in results if r.success)
        print(f"""
📊 Результаты группы {batch_num}:
• Успешно: {successful}/{len(batch)}
• С ошибками: {len(batch) - successful}
""")

        if batch_num < len(account_batches):
            print("⏳ Пауза между группами...")
            await asyncio.sleep(10)

    # Сохраняем общий статус
    await save_auth_status(all_results)

    # Итоговая статистика
    total_successful = sum(1 for r in all_results if r.success)
    total_sessions = sum(1 for r in all_results if r.session_created)

    print(f"""
📊 Итоги авторизации:
===========================================
✅ Успешно авторизовано: {total_successful}/{len(ACCOUNTS)}
📁 Создано сессий: {total_sessions}
❌ Ошибок: {len(ACCOUNTS) - total_successful}

🔍 Статус аккаунтов:""")

    for result in all_results:
        status = "✅" if result.success else "❌"
        error_info = f" ({result.error})" if result.error else ""
        print(f"{status} {result.phone}{error_info}")

    print("""
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
        print(f"\n❌ Критическая ошибка: {str(e)}")
    finally:
        print("\n👋 Программа завершена")