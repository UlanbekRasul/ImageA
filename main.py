# main.py

import subprocess
import os
import signal
import sys
import time
import json
import datetime
from typing import Optional, Dict, List
from tracking import UserTracker


def cleanup_files():
    """Очищает файлы обмена данными при запуске"""
    for file in ['command.json', 'result.json']:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Файл {file} очищен")
            except Exception as e:
                print(f"❌ Ошибка при очистке {file}: {str(e)}")


def check_session_files() -> List[str]:
    """Проверяет наличие файлов сессий"""
    session_files = [f for f in os.listdir() if f.endswith('.session')]
    if not session_files:
        print("""
⚠️ Файлы сессий не найдены!
📱 Сначала запустите auth_accounts.py для авторизации аккаунтов
""")
    return session_files


def check_config_files() -> bool:
    """Проверяет наличие необходимых конфигурационных файлов"""
    required_files = ['config.py', 'tracking.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        print(f"""
❌ Отсутствуют необходимые файлы:
{chr(10).join(f'• {f}' for f in missing_files)}
""")
        return False
    return True


def initialize_tracker() -> Optional[UserTracker]:
    """Инициализирует систему отслеживания"""
    try:
        tracker = UserTracker()
        stats = tracker.get_overall_stats()
        print(f"""
📊 Статистика системы:
• Всего добавлено: {stats['total_added_all_time']}
• За последние 24ч: {stats['total_added_24h']}
• Доступно аккаунтов: {stats['accounts_available']}
""")
        return tracker
    except Exception as e:
        print(f"❌ Ошибка инициализации трекера: {str(e)}")
        return None


def start_processes() -> Dict[str, subprocess.Popen]:
    """Запускает необходимые процессы"""
    processes = {}
    try:
        # Запуск telebot процесса
        processes['telebot'] = subprocess.Popen(
            ["python", "telebot_process.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ Telebot процесс запущен")

        # Запуск telethon процесса
        processes['telethon'] = subprocess.Popen(
            ["python", "telethon_process.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ Telethon процесс запущен")

    except Exception as e:
        print(f"❌ Ошибка запуска процессов: {str(e)}")

    return processes


def monitor_processes(processes: Dict[str, subprocess.Popen]):
    """Мониторит запущенные процессы"""
    while True:
        try:
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"⚠️ Процесс {name} остановлен, перезапуск...")

                    # Читаем вывод для диагностики
                    stdout, stderr = process.communicate()
                    if stdout:
                        print(f"Вывод {name}:\n{stdout.decode()}")
                    if stderr:
                        print(f"Ошибки {name}:\n{stderr.decode()}")

                    # Перезапускаем процесс
                    processes[name] = subprocess.Popen(
                        ["python", f"{name}_process.py"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    print(f"✅ Процесс {name} перезапущен")

            time.sleep(5)

        except KeyboardInterrupt:
            print("\n⚠️ Получен сигнал завершения")
            cleanup_processes(processes)
            break
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {str(e)}")
            time.sleep(5)


def cleanup_processes(processes: Dict[str, subprocess.Popen]):
    """Корректно завершает все процессы"""
    print("\n🔄 Завершение процессов...")

    for name, process in processes.items():
        try:
            process.terminate()
            print(f"✅ Процесс {name} остановлен")
        except Exception as e:
            print(f"❌ Ошибка при остановке {name}: {str(e)}")

    # Очищаем файлы обмена данными
    cleanup_files()


def main():
    print("""
🚀 Запуск системы инвайтинга
================================
""")

    # Проверка конфигурации
    if not check_config_files():
        return

    # Проверка сессий
    session_files = check_session_files()
    if not session_files:
        return

    # Очистка старых файлов
    cleanup_files()

    # Инициализация трекера
    tracker = initialize_tracker()
    if not tracker:
        return

    # Запуск процессов
    processes = start_processes()
    if not processes:
        return
#h

    print("""
✅ Система запущена успешно
📱 Доступные команды в боте:
• /status - Статус системы
• /add - Добавить пользователей
• /help - Список всех команд
""")

    # Мониторинг процессов
    try:
        monitor_processes(processes)
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
    finally:
        cleanup_processes(processes)
        print("\n👋 Система остановлена")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Программа завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")


# 1. Удалить все сессии
#rm *.session

# 2. Удалить файлы команд
#rm command.json result.json

# 3. Запустить авторизацию
#python auth_accounts.py

# 4. После успешной авторизации запустить бота
#python main.py

