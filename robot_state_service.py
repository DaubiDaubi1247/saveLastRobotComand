from dataclasses import dataclass
from typing import List
from robot_state_repository import RobotStateRepository, RobotStateDB


@dataclass
class RobotState:
    """Модель данных для API (обработанные данные)"""
    workshop: str
    robot: str


class RobotStateService:
    """Сервис для обработки данных о роботах"""

    def __init__(self, repository: RobotStateRepository):
        self._repository = repository

    def _extract_workshop(self, robot_name: str) -> str:
        """
        Извлечь номер цеха из имени робота.

        Формат имени: W{цех}...
        Например: W8R1 -> цех 8, W1R2 -> цех 1

        Args:
            robot_name: Имя робота

        Returns:
            Номер цеха как строка
        """
        if len(robot_name) >= 2 and robot_name[0] == 'W':
            return robot_name[1]
        return ""

    def _map_to_robot_state(self, db_state: RobotStateDB) -> RobotState:
        """Преобразование сырых данных из БД в модель для API"""
        return RobotState(
            workshop=self._extract_workshop(db_state.robot),
            robot=db_state.robot
        )

    def get_robot_state(self, robot: str) -> RobotState:
        """
        Получить состояние конкретного робота.

        Args:
            robot: Имя робота

        Returns:
            RobotState с данными о роботе
        """
        db_state = self._repository.get_robot_state(robot)
        if db_state is None:
            return RobotState(workshop="", robot=robot)
        return self._map_to_robot_state(db_state)

    def get_all_robots_state(self) -> List[RobotState]:
        """
        Получить состояние всех роботов.

        Returns:
            Список RobotState для всех роботов
        """
        db_states = self._repository.get_all_robots_state()
        return [self._map_to_robot_state(s) for s in db_states]
