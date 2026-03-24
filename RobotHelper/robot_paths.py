"""Пути к папкам на роботе и локальные пути."""
from enum import Enum


class RobotProgramPath(str, Enum):
    """Пути к папкам программ на роботе KRC."""
    WORK = r"KRC:\R1\Program\work"
    GENERATED = r"KRC:\R1\Program\generated"
    SERVICE = r"KRC:\R1\Program\service"


class LocalPath(str, Enum):
    """Локальные пути для сохранения файлов."""
    BASE_DIR = "robot_files"
    WORK_SUBDIR = "work"
    GENERATED_SUBDIR = "generated"