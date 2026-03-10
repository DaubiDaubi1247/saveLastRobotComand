from dataclasses import dataclass
from typing import List, Optional
import re
from RobotStateRepository.robot_state_repository import RobotStateRepository, RobotStateDB, RobotProgramDB
from RobotStateRepository.program_file_repository import ProgramFileRepository


@dataclass
class RobotState:
    workshop: str
    robot: str


@dataclass
class RobotProgram:
    robot: str
    program_name: Optional[str] = None
    snr_c: Optional[int] = None
    program_line: Optional[str] = None
    point_name: Optional[str] = None


class RobotStateService:

    def __init__(self, repository: RobotStateRepository, file_repository: ProgramFileRepository):
        self._repository = repository
        self._file_repository = file_repository
        self._point_pattern = re.compile(r'[XY]?([SW])(\d+)_\d+')

    def _extract_workshop(self, robot_name: str) -> str:
        if len(robot_name) >= 2 and robot_name[0] == 'W':
            return robot_name[1]
        return ""

    def _extract_point_info(self, line: str) -> Optional[str]:
        if not line:
            return None

        match = self._point_pattern.search(line)
        if match:
            return f"{match.group(1)}{match.group(2)}".lower()

        return None

    def _map_to_robot_state(self, db_state: RobotStateDB) -> RobotState:
        return RobotState(
            workshop=self._extract_workshop(db_state.robot),
            robot=db_state.robot
        )

    def _map_to_robot_program(self, db_state: RobotProgramDB) -> RobotProgram:
        program_line = None
        point_name = None

        if db_state.program_names and db_state.snr_c:
            program_line = self._file_repository.get_line(
                db_state.program_names,
                db_state.snr_c,
                db_state.robot
            )
            point_name = self._extract_point_info(program_line)
        else:
            db_state.program_names = None
            db_state.snr_c = None

        return RobotProgram(
            robot=db_state.robot,
            program_name=db_state.program_names,
            snr_c=db_state.snr_c,
            program_line=program_line,
            point_name=point_name
        )

    def get_robot_state(self, robot: str) -> RobotState:
        db_state = self._repository.get_robot_state(robot)
        if db_state is None:
            return RobotState(workshop="", robot=robot)
        return self._map_to_robot_state(db_state)

    def get_all_robots_state(self) -> List[RobotState]:
        db_states = self._repository.get_all_robots_state()
        return [self._map_to_robot_state(s) for s in db_states]

    def get_robot_program(self, robot: str) -> RobotProgram:
        db_state = self._repository.get_robot_program_info(robot)
        if db_state is None:
            return RobotProgram(robot=robot)
        return self._map_to_robot_program(db_state)
