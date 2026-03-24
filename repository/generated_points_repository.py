from typing import Dict, List, Optional, Any, Tuple
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_paths import RobotProgramPath
from RobotHelper.robot_poller import ROBOTS
import re


class GeneratedPointsRepository:

    def __init__(self):
        # Паттерн для поиска вызовов функций (игнорируем custom_sync)
        # Ищем строки вида: edge_1_left_mte()
        self._function_call_pattern = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)")
        self._custom_sync_pattern = re.compile(r"^\s*custom_sync\s*\(")

    def _get_robot_config(self, robot_name: str) -> Optional[Dict[str, Any]]:
        config = ROBOTS.get(robot_name)
        if not config:
            return None
        return {
            "addr": config[0],
            "port": config[1],
            "timeout": config[2] / 1000.0
        }

    def _get_dat_files_order(self, connector: RobotConnector) -> List[str]:
        """
        Получает порядок .dat файлов из main_gen.src.
        Возвращает список имен .dat файлов в порядке вызова функций.
        """
        # Скачиваем main_gen.src
        file_path = f"{RobotProgramPath.GENERATED.value}\\main_gen.src"
        content = connector._copy_file_to_mem(file_path)
        
        if not content:
            return []
        
        dat_files_order: List[str] = []
        lines = content.split('\n')
        
        for line in lines:
            # Пропускаем custom_sync
            if self._custom_sync_pattern.search(line):
                continue
            
            # Ищем вызовы функций
            match = self._function_call_pattern.search(line)
            if match:
                function_name = match.group(1)
                # Проверяем, есть ли соответствующий .dat файл
                dat_file_name = f"{function_name}.dat"
                dat_files_order.append(dat_file_name)
        
        return dat_files_order

    def get_robot_points(self, robot_name: str) -> List[Dict[str, Any]]:
        config = self._get_robot_config(robot_name)
        if not config:
            return []

        connector = RobotConnector(
            addr=config["addr"],
            port=config["port"],
            timeout=config.get("timeout", 3.0)
        )
        try:
            connector.connect()
            connector.authenticate()
            
            # Получаем порядок .dat файлов из main_gen.src
            dat_files_order = self._get_dat_files_order(connector)
            
            # Получаем все точки из .dat файлов
            all_points = connector.get_dat_points_by_file(directory=RobotProgramPath.GENERATED)
            
            # Формируем результат в порядке файлов
            result: List[Dict[str, Any]] = []
            for dat_file in dat_files_order:
                if dat_file in all_points:
                    result.append({
                        "file_name": dat_file,
                        "points": all_points[dat_file]
                    })
            
            return result
        except Exception as e:
            raise RuntimeError(f"Ошибка получения generated точек для робота {robot_name}: {e}")
        finally:
            connector.disconnect()
