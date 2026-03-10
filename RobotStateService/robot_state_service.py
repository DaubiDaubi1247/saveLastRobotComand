from dataclasses import dataclass
from typing import List, Optional
from RobotStateRepository.robot_state_repository import RobotStateRepository, RobotStateDB
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


class RobotStateService:

    def __init__(self, repository: RobotStateRepository, file_repository: ProgramFileRepository):
        self._repository = repository
        self._file_repository = file_repository

    def _extract_workshop(self, robot_name: str) -> str:
        if len(robot_name) >= 2 and robot_name[0] == 'W':
            return robot_name[1]
        return ""

    def _map_to_robot_state(self, db_state: RobotStateDB) -> RobotState:
        return RobotState(
            workshop=self._extract_workshop(db_state.robot),
            robot=db_state.robot
        )

    def _map_to_robot_program(self, db_state: RobotStateDB) -> RobotProgram:
        program_line = None
        if db_state.program_names and db_state.snr_c:
            program_line = self._file_repository.get_line(db_state.program_names, db_state.snr_c)

        return RobotProgram(
            robot=db_state.robot,
            program_name=db_state.program_names,
            snr_c=db_state.snr_c,
            program_line=program_line
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

    def get_all_robots_programs(self) -> List[RobotProgram]:
        db_states = self._repository.get_all_robots_state()
        return [self._map_to_robot_program(s) for s in db_states]
