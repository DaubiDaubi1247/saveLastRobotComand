import os
import shutil
import threading
from enum import Enum
from typing import Optional, List, Literal
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_paths import RobotProgramPath, LocalPath
from RobotHelper.robot_poller import ROBOTS


class ProgramSource(str, Enum):
    """Перечисление источников программ робота."""
    WORK = "work"
    GENERATED = "generated"


class ProgramFileRepository:

    def __init__(self, base_dir: str = LocalPath.BASE_DIR):
        self._base_dir = base_dir

    def _cleanup_opposite_folder(self, robot_name: str, source: ProgramSource) -> None:
        """Удалить содержимое противоположной папки."""
        opposite = ProgramSource.GENERATED if source == ProgramSource.WORK else ProgramSource.WORK
        robot_dir = os.path.join(LocalPath.BASE_DIR, robot_name)
        opposite_dir = os.path.join(robot_dir, opposite.value)

        if os.path.exists(opposite_dir):
            shutil.rmtree(opposite_dir)

    def _get_local_work_files(self, robot_name: str) -> List[str]:
        """Получить список .src файлов в локальной папке work робота."""
        robot_dir = os.path.join(self._base_dir, robot_name)
        work_dir = os.path.join(robot_dir, LocalPath.WORK_SUBDIR)
        if not os.path.exists(work_dir):
            return []
        
        files = []
        for root, dirs, filenames in os.walk(work_dir):
            for file in filenames:
                if file.upper().endswith('.SRC'):
                    files.append(file.upper())
        return files

    def check_file_on_robot(self, program_name: str, robot_name: str, source: ProgramSource) -> bool:
        """Проверить, есть ли файл программы на роботе в указанной папке."""
        config = ROBOTS.get(robot_name)
        if not config:
            return False

        addr = config[0]
        port = config[1]

        directory = RobotProgramPath.WORK if source == ProgramSource.WORK else RobotProgramPath.GENERATED

        connector = RobotConnector(addr=addr, port=port, timeout=5.0)
        try:
            connector.connect()
            connector.authenticate()
            file_list = connector.get_file_list(directory)

            program_name_upper = program_name.upper()
            if not program_name_upper.endswith('.SRC'):
                program_name_upper += '.SRC'
            file_name_only = os.path.basename(program_name_upper.replace('\\', '/'))

            for file in file_list:
                if file.upper() == file_name_only or file.upper() == program_name_upper:
                    return True
            return False
        except Exception:
            return False
        finally:
            connector.disconnect()

    def check_file_in_service(self, program_name: str, robot_name: str) -> bool:
        config = ROBOTS.get(robot_name)
        if not config:
            return False

        addr = config[0]
        port = config[1]

        connector = RobotConnector(addr=addr, port=port, timeout=5.0)
        try:
            connector.connect()
            connector.authenticate()
            file_list = connector.get_file_list(RobotProgramPath.SERVICE)

            program_name_upper = program_name.upper()
            if not program_name_upper.endswith('.SRC'):
                program_name_upper += '.SRC'
            file_name_only = os.path.basename(program_name_upper.replace('\\', '/'))

            for file in file_list:
                if file.upper() == file_name_only or file.upper() == program_name_upper:
                    return True
            return False
        except Exception:
            return False
        finally:
            connector.disconnect()

    def download_robot_files(self, robot_name: str, download_work: bool = True, download_generated: bool = True) -> None:
        config = ROBOTS.get(robot_name)
        if not config:
            return

        addr = config[0]
        port = config[1]

        robot_dir = os.path.join(self._base_dir, robot_name)

        connector = RobotConnector(addr=addr, port=port, timeout=5.0)
        try:
            connector.connect()
            connector.authenticate()

            if download_work:
                # Получаем список файлов с робота
                robot_file_list = connector.get_file_list(RobotProgramPath.WORK)
                robot_src_files = set(f.upper() for f in robot_file_list if f.upper().endswith('.SRC'))

                # Получаем список локальных файлов
                local_files = self._get_local_work_files(robot_name)

                # Сравниваем списки
                if local_files and robot_src_files == set(local_files):
                    # Списки совпадают — файлы уже актуальны, не скачиваем заново
                    pass
                else:
                    # Списки отличаются или файлов нет — удаляем и скачиваем заново
                    if os.path.exists(robot_dir):
                        work_dir = os.path.join(robot_dir, LocalPath.WORK_SUBDIR)
                        if os.path.exists(work_dir):
                            shutil.rmtree(work_dir)
                    connector.copy_work_files(output_dir=self._base_dir, robot_name=robot_name, process_src=True)

            if download_generated:
                connector.get_file_list(RobotProgramPath.GENERATED)
                connector.copy_generated_files(output_dir=self._base_dir, robot_name=robot_name, process_src=True)
        except Exception as e:
            raise RuntimeError(f"Ошибка при скачивании файлов с робота {robot_name}: {e}")
        finally:
            connector.disconnect()

    def _find_file(self, program_name: str, robot_name: Optional[str] = None, source: Optional[ProgramSource] = None) -> Optional[str]:
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
                    return None 
                else:
                    # Ищем во всех подпапках робота
                    for root, dirs, files in os.walk(robot_dir):
                        for file in files:
                            if file.upper() == file_name_only or file.upper() == program_name:
                                return os.path.join(root, file)
                    return None
        return None

    def get_line(self, program_name: str, line_number: int, robot_name: Optional[str] = None, source: Optional[ProgramSource] = None, cleanup_opposite: bool = False) -> Optional[str]:
        file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path and robot_name:
            self.download_robot_files(
                robot_name,
                download_work=(source != ProgramSource.GENERATED),
                download_generated=(source == ProgramSource.GENERATED)
            )
            file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path:
            return None

        # Если файл найден и указана очистка — запустить в фоне
        if cleanup_opposite and source and robot_name:
            threading.Thread(
                target=self._cleanup_opposite_folder,
                args=(robot_name, source),
                daemon=True
            ).start()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if 0 < line_number <= len(lines):
                    return lines[line_number - 1].rstrip('\n')
        except Exception:
            pass

        return None

    def get_line_with_fold_context(self, program_name: str, line_number: int, robot_name: Optional[str] = None, source: Optional[ProgramSource] = None, cleanup_opposite: bool = False) -> tuple[Optional[str], Optional[str]]:
        file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path and robot_name:
            self.download_robot_files(
                robot_name,
                download_work=(source != ProgramSource.GENERATED),
                download_generated=(source == ProgramSource.GENERATED)
            )
            file_path = self._find_file(program_name, robot_name, source=source)

        if not file_path:
            return None, None

        # Если файл найден и указана очистка — запустить в фоне
        if cleanup_opposite and source and robot_name:
            threading.Thread(
                target=self._cleanup_opposite_folder,
                args=(robot_name, source),
                daemon=True
            ).start()

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
