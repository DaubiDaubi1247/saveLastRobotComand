from typing import Any, Dict, List
from repository.robot_points_repository import RobotPointsRepository
from repository.generated_points_repository import GeneratedPointsRepository


class RobotPointsService:

    def __init__(self, repository: RobotPointsRepository, generated_repository: GeneratedPointsRepository):
        self._repository = repository
        self._generated_repository = generated_repository

    def get_robot_points(self, robot_name: str) -> Dict[str, Dict[str, List[List[float]]]]:
        return self._repository.get_robot_points(robot_name)

    def get_robot_points_generated(self, robot_name: str) -> List[Dict[str, Any]]:
        points = self._generated_repository.get_robot_points(robot_name)
        return [{"file_name": k, "points": v} for k, v in points.items()]
