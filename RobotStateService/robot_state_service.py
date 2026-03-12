from dataclasses import dataclass
from typing import List, Optional, Literal
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

    def download_robot_files(self, robot_name: str, download_work: bool = True, download_generated: bool = False) -> None:
        self._file_repository.download_robot_files(robot_name, download_work, download_generated)

    def _extract_workshop(self, robot_name: str) -> str:
        if len(robot_name) >= 2 and robot_name[0] == 'W':
            return robot_name[1]
        return ""

    def _extract_point_info(self, line: str) -> Optional[str]:
        if not line:
            return None

        # Для FOLD строк вида ";FOLD LIN S1_4 ... ;%{PE}" или ";FOLD ARCSWI ... LIN W8_5 ..."
        fold_match = re.match(r'^\s*;FOLD\s+(.+?)$', line, re.IGNORECASE)
        if fold_match:
            fold_content = fold_match.group(1)
            match = self._point_pattern.search(fold_content)
            if match:
                return f"{match.group(1)}{match.group(2)}".lower()
            return None

        # Для обычных строк ищем точку в строке
        match = self._point_pattern.search(line)
        if match:
            return f"{match.group(1)}{match.group(2)}".lower()

        return None

    def _map_to_robot_state(self, db_state: RobotStateDB) -> RobotState:
        return RobotState(
            workshop=self._extract_workshop(db_state.robot),
            robot=db_state.robot
        )

    def _map_to_robot_program(self, db_state: RobotProgramDB, source: Optional[Literal["work", "generated"]] = None) -> RobotProgram:
        program_line = None
        point_name = None
        fold_line = None

        if db_state.program_names and db_state.snr_c:
            current_line, fold_line = self._file_repository.get_line_with_fold_context(
                db_state.program_names,
                db_state.snr_c,
                db_state.robot,
                source=source
            )
            if current_line is None and fold_line is None and source:
                # Файл не найден в указанной папке
                folder_name = "generated" if source == "generated" else "work"
                raise FileNotFoundError(f"Исполняемый файл '{db_state.program_names}' не найден в папке {folder_name}, проверьте корректность выбранного метода загрузки программы")
            program_line = fold_line if fold_line else current_line
            line_for_point = fold_line if fold_line else current_line
            point_name = self._extract_point_info(line_for_point)
        else:
            db_state.program_names = None
            db_state.snr_c = None

        return RobotProgram(
            robot=db_state.robot,
            program_name=db_state.program_names,
            program_line=program_line,
            snr_c=db_state.snr_c,
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

    def get_robot_program(self, robot: str, source: Optional[Literal["work", "generated"]] = None) -> RobotProgram:
        db_state = self._repository.get_robot_program_info(robot)
        if db_state is None:
            return RobotProgram(robot=robot)
        return self._map_to_robot_program(db_state, source=source)
