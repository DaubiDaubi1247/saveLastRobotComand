"""Конфигурация приложения."""
import os
from typing import Dict, Tuple
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


def _parse_robots_config() -> Dict[str, Tuple[str, int, int, str]]:
    """Парсит конфигурацию роботов из переменных окружения."""
    robots = {}
    prefix = "ROBOT_"
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            robot_name = key[len(prefix):]
            parts = value.split(":")
            if len(parts) == 4:
                ip, port, timeout, tag = parts
                robots[robot_name] = (ip, int(port), int(timeout), tag)
    
    return robots


# Настройки сервера
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

# Настройки InfluxDB
INFLUX_HOST = os.getenv("INFLUX_HOST", "192.168.22.11")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", "8086"))
INFLUX_USERNAME = os.getenv("INFLUX_USERNAME", "user")
INFLUX_PASSWORD = os.getenv("INFLUX_PASSWORD", "pass")
INFLUX_DATABASE = os.getenv("INFLUX_DATABASE", "influx")

# Настройки Telegraf
TELEGRAF_HOST = os.getenv("TELEGRAF_HOST", "192.168.22.11")
TELEGRAF_PORT = int(os.getenv("TELEGRAF_PORT", "8092"))

# Интервал опроса роботов (секунды)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))

# Ключ аутентификации для роботов
ROBOT_AUTH_KEY = os.getenv("ROBOT_AUTH_KEY", "My_example_KEY")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "robot_server.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Конфигурация роботов по умолчанию (если не заданы в .env)
_DEFAULT_ROBOTS: Dict[str, Tuple[str, int, int, str]] = {
    'W8R1': ('10.1.0.82', 3333, 2000, 'W8R1'),
    'W8R2': ('10.1.0.84', 3333, 2000, 'W8R2'),
    'W8R3': ('10.1.0.86', 3333, 2000, 'W8R3'),
    'W8R4': ('10.1.0.88', 3333, 2000, 'W8R4'),
    'W1R1': ('10.1.0.14', 3333, 2000, 'W1R1'),
    'W1R2': ('10.1.0.16', 3333, 2000, 'W1R2'),
    'W2R1': ('10.1.0.44', 3333, 2000, 'W2R1'),
    'W2R2': ('10.1.0.46', 3333, 2000, 'W2R2'),
    'W1x4R1': ('10.1.0.32', 4444, 2000, 'W1x4R1'),
    'W1x4R2': ('10.1.0.34', 3333, 2000, 'W1x4R2'),
    'W1x4R3': ('10.1.0.36', 4444, 2000, 'W1x4R3'),
    'W1x4R4': ('10.1.0.38', 3333, 2000, 'W1x4R4'),
    'W8R5': ('10.1.0.117', 3333, 2000, 'W8R5'),
    'W7R1': ('10.1.0.71', 3333, 2000, 'W7R1'),
    'W1R7': ('10.1.0.18', 3333, 2000, 'W1R7'),
    'W2R6': ('10.1.0.26', 3333, 2000, 'W2R6'),
    'test': ('192.168.6.197', 3333, 2000, 'test')
}

# Конфигурация роботов: из .env или значения по умолчанию
ROBOTS = _parse_robots_config() or _DEFAULT_ROBOTS
