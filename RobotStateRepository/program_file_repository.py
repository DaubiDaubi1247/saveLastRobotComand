import os
from typing import Optional, List


class ProgramFileRepository:

    def __init__(self, base_dir: str = "robot_files"):
        self._base_dir = base_dir

    def _find_file(self, program_name: str) -> Optional[str]:
        program_name = program_name.upper()
        if not program_name.endswith('.SRC'):
            program_name += '.SRC'

        for root, dirs, files in os.walk(self._base_dir):
            for file in files:
                if file.upper() == program_name:
                    return os.path.join(root, file)

        normalized = program_name.lstrip('\\/')
        normalized = normalized.replace('/', os.sep).replace('\\', os.sep)
        full_path = os.path.join(self._base_dir, normalized)
        if os.path.exists(full_path):
            return full_path

        return None

    def get_line(self, program_name: str, line_number: int) -> Optional[str]:
        file_path = self._find_file(program_name)
        if not file_path:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if 0 < line_number <= len(lines):
                    return lines[line_number - 1].rstrip('\n')
        except Exception:
            pass

        return None

    def get_file_content(self, program_name: str) -> Optional[List[str]]:
        file_path = self._find_file(program_name)
        if not file_path:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception:
            pass

        return None
