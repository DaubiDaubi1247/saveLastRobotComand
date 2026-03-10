from typing import Optional, List
from RobotStateRepository.program_file_repository import ProgramFileRepository


class ProgramFileService:

    def __init__(self, repository: ProgramFileRepository):
        self._repository = repository

    def get_program_line(self, program_name: str, line_number: int) -> Optional[str]:
        return self._repository.get_line(program_name, line_number)

    def get_program_content(self, program_name: str) -> Optional[List[str]]:
        return self._repository.get_file_content(program_name)
