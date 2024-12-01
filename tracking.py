# tracking.py

import datetime
from collections import defaultdict
import json
import os


class UserTracker:
    def __init__(self, storage_file='user_tracking.json'):
        self.storage_file = storage_file
        self.account_stats = defaultdict(lambda: {
            'total_added': 0,
            'last_used': None,
            'next_available': None,
            'addition_history': [],
            'failed_attempts': 0,
            'successful_adds': []
        })
        self.load_stats()

    def load_stats(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for phone, stats in data.items():
                    stats['last_used'] = (datetime.datetime.fromisoformat(stats['last_used'])
                                          if stats['last_used'] else None)
                    stats['next_available'] = (datetime.datetime.fromisoformat(stats['next_available'])
                                               if stats['next_available'] else None)
                    self.account_stats[phone].update(stats)

    def save_stats(self):
        data = {}
        for phone, stats in self.account_stats.items():
            data[phone] = stats.copy()
            data[phone]['last_used'] = (stats['last_used'].isoformat()
                                        if stats['last_used'] else None)
            data[phone]['next_available'] = (stats['next_available'].isoformat()
                                             if stats['next_available'] else None)

        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_addition(self, phone, users_added, target_channel):
        current_time = datetime.datetime.now()
        cooldown_hours = 12

        self.account_stats[phone]['total_added'] += users_added
        self.account_stats[phone]['last_used'] = current_time
        self.account_stats[phone]['next_available'] = current_time + datetime.timedelta(hours=cooldown_hours)

        addition_record = {
            'timestamp': current_time.isoformat(),
            'users_added': users_added,
            'target_channel': target_channel
        }
        self.account_stats[phone]['addition_history'].append(addition_record)
        self.account_stats[phone]['successful_adds'].extend([current_time.isoformat()] * users_added)

        self.save_stats()

    def record_failed_attempt(self, phone):
        self.account_stats[phone]['failed_attempts'] += 1
        self.save_stats()

    def get_account_status(self, phone):
        stats = self.account_stats[phone]
        current_time = datetime.datetime.now()

        # Сброс счетчика если прошло 12 часов
        if stats['last_used'] and (current_time - stats['last_used']).total_seconds() >= 12 * 3600:
            stats['total_added'] = 0
            stats['last_used'] = None
            stats['next_available'] = None
            self.save_stats()

        else:
            time_remaining = stats['next_available'] - current_time
            status = "Cooling down"

        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)
        seconds = int(time_remaining.total_seconds() % 60)

        return {
            'status': status,
            'total_added': stats['total_added'],
            'remaining_capacity': max(0, 50 - stats['total_added']),
            'time_remaining': {
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds
            },
            'failed_attempts': stats['failed_attempts'],
            'last_24h_adds': len([add_time for add_time in stats['successful_adds']
                                  if
                                  (current_time - datetime.datetime.fromisoformat(add_time)).total_seconds() <= 86400])
        }

    def verify_addition(self, phone, expected_count, actual_count, target_channel):
        """Проверяет и регистрирует фактическое количество добавленных пользователей"""
        if actual_count != expected_count:
            self.record_failed_attempt(phone)

        self.record_addition(phone, actual_count, target_channel)
        return actual_count == expected_count

    def get_next_batch_time(self, account_phone):
        stats = self.account_stats[account_phone]
        current_time = datetime.datetime.now()

        if not stats['next_available']:
            return None

        if current_time >= stats['next_available']:
            return current_time

        return stats['next_available']

    def get_overall_stats(self):
        current_time = datetime.datetime.now()
        total_added_24h = sum(
            len([add_time for add_time in stats['successful_adds']
                 if (current_time - datetime.datetime.fromisoformat(add_time)).total_seconds() <= 86400])
            for stats in self.account_stats.values()
        )

        return {
            'total_added_all_time': sum(stats['total_added'] for stats in self.account_stats.values()),
            'total_added_24h': total_added_24h,
            'total_failed_attempts': sum(stats['failed_attempts'] for stats in self.account_stats.values()),
            'accounts_available': sum(1 for stats in self.account_stats.values()
                                      if not stats['next_available'] or current_time >= stats['next_available'])
        }
