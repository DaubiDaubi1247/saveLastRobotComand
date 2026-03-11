import os
from typing import Optional, List
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_poller import ROBOTS


class ProgramFileRepository:

    def __init__(self, base_dir: str = "robot_files"):
        self._base_dir = base_dir

    def _download_robot_files(self, robot_name: str) -> None:
        config = ROBOTS.get(robot_name)
        if not config:
            return

        addr = config[0]
        port = config[1]

        connector = RobotConnector(addr=addr, port=port, timeout=5.0)
        try:
            connector.connect()
            connector.authenticate()
            connector.get_file_list()
            connector.copy_files_to_local(output_dir=self._base_dir, robot_name=robot_name, process_src=True)
        except Exception:
            pass
        finally:
            connector.disconnect()

    def _find_file(self, program_name: str, robot_name: Optional[str] = None) -> Optional[str]:
        if not program_name:
            return None
            
        program_name = program_name.upper()
        if not program_name.endswith('.SRC'):
            program_name += '.SRC'

        # Очищаем путь от ведущих /R1/ и т.д., оставляем только имя файла
        file_name_only = os.path.basename(program_name.replace('\\', '/'))

        # Если указан robot_name, ищем в его папке
        if robot_name:
            robot_dir = os.path.join(self._base_dir, robot_name)
            if os.path.exists(robot_dir):
                for root, dirs, files in os.walk(robot_dir):
                    for file in files:
                        if file.upper() == file_name_only or file.upper() == program_name:
                            return os.path.join(root, file)

        # Если не нашли или robot_name не указан, ищем во всех папках
        for root, dirs, files in os.walk(self._base_dir):
            for file in files:
                if file.upper() == file_name_only or file.upper() == program_name:
                    return os.path.join(root, file)

        # Пробуем найти по полному пути
        normalized = program_name.lstrip('\\/')
        normalized = normalized.replace('/', os.sep).replace('\\', os.sep)
        full_path = os.path.join(self._base_dir, normalized)
        if os.path.exists(full_path):
            return full_path

        return None

    def get_line(self, program_name: str, line_number: int, robot_name: Optional[str] = None) -> Optional[str]:
        file_path = self._find_file(program_name, robot_name)
        
        if not file_path and robot_name:
            self._download_robot_files(robot_name)
            file_path = self._find_file(program_name, robot_name)
        
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

    def get_line_with_fold_context(self, program_name: str, line_number: int, robot_name: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        file_path = self._find_file(program_name, robot_name)
        
        if not file_path and robot_name:
            self._download_robot_files(robot_name)
            file_path = self._find_file(program_name, robot_name)
        
        if not file_path:
            return None, None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                if not (0 < line_number <= len(lines)):
                    return None, None
                
                current_line = lines[line_number - 1].rstrip('\n')
                
                # Ищем ближайший ;FOLD выше текущей строки (пропуская FOLD Parameters)
                fold_line = None
                
                for i in range(line_number - 2, -1, -1):
                    line = lines[i].strip()
                    if line.startswith(';FOLD'):
                        # Пропускаем FOLD Parameters
                        if 'Parameters' not in line:
                            # Убираем ";FOLD " из начала и всё после ";" в конце
                            fold_line = line[5:].strip() if line.startswith(';FOLD ') else line[1:].strip()
                            # Убираем всё после ";" (включительно)
                            semicolon_index = fold_line.find(';')
                            if semicolon_index != -1:
                                fold_line = fold_line[:semicolon_index].strip()
                            break
                
                return current_line, fold_line
                
        except Exception:
            pass

        return None, None

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
