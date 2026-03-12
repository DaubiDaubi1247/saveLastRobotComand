import os
import shutil
from typing import Optional, List, Literal
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_poller import ROBOTS


class ProgramFileRepository:

    def __init__(self, base_dir: str = "robot_files"):
        self._base_dir = base_dir

    def download_robot_files(self, robot_name: str, download_work: bool = True, download_generated: bool = True) -> None:
        config = ROBOTS.get(robot_name)
        if not config:
            return

        addr = config[0]
        port = config[1]

        robot_dir = os.path.join(self._base_dir, robot_name)
        if os.path.exists(robot_dir):
            shutil.rmtree(robot_dir)
        
        connector = RobotConnector(addr=addr, port=port, timeout=5.0)
        try:
            connector.connect()
            connector.authenticate()

            if download_work:
                connector.get_file_list("KRC:\\R1\\Program\\work")
                connector.copy_work_files(output_dir=self._base_dir, robot_name=robot_name, process_src=True)

            if download_generated:
                connector.get_file_list("KRC:\\R1\\Program\\generated")
                connector.copy_generated_files(output_dir=self._base_dir, robot_name=robot_name)
        except Exception as e:
            raise RuntimeError(f"Failed to download files from robot {robot_name}: {e}")
        finally:
            connector.disconnect()

    def _find_file(self, program_name: str, robot_name: Optional[str] = None, source: Optional[Literal["work", "generated"]] = None) -> Optional[str]:
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
                # Если указан source, ищем только в соответствующей подпапке
                if source:
                    source_dir = os.path.join(robot_dir, source)
                    if os.path.exists(source_dir):
                        for root, dirs, files in os.walk(source_dir):
                            for file in files:
                                if file.upper() == file_name_only or file.upper() == program_name:
                                    return os.path.join(root, file)
                    return None  # Файл в указанном source не найден
                else:
                    # Ищем во всех подпапках
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

    def find_program_file(self, program_name: str, robot_name: str, source: Literal["work", "generated"]) -> Optional[str]:
        """
        Ищет файл программы в указанной папке (work или generated).
        Возвращает путь к файлу или None, если файл не найден.
        """
        return self._find_file(program_name, robot_name, source=source)

    def get_line(self, program_name: str, line_number: int, robot_name: Optional[str] = None, source: Optional[Literal["work", "generated"]] = None) -> Optional[str]:
        file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path and robot_name:
            self.download_robot_files(robot_name, download_work=(source != "generated"), download_generated=(source == "generated"))
            file_path = self._find_file(program_name, robot_name, source=source)

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

    def get_line_with_fold_context(self, program_name: str, line_number: int, robot_name: Optional[str] = None, source: Optional[Literal["work", "generated"]] = None) -> tuple[Optional[str], Optional[str]]:
        file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path and robot_name:
            self.download_robot_files(robot_name, download_work=(source != "generated"), download_generated=(source == "generated"))
            file_path = self._find_file(program_name, robot_name, source=source)

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
