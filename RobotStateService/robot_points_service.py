from typing import Any, Dict, List
from RobotStateRepository.robot_points_repository import RobotPointsRepository


class RobotPointsService:

    def __init__(self, repository: RobotPointsRepository):
        self._repository = repository

    def get_robot_points(self, robot_name: str) -> Dict[str, Dict[str, List[List[float]]]]:
        return self._repository.get_robot_points(robot_name)
