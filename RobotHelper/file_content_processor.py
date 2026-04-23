#!/usr/bin/env python3
import re
from typing import Dict, List, Set, Tuple, Union


class FileContentProcessor:

    def __init__(self):
        self._coords_pattern = re.compile(
            r'X\s*(-?\d+\.?\d*),\s*Y\s*(-?\d+\.?\d*),\s*Z\s*(-?\d+\.?\d*)'
        )
        self._name_pattern = re.compile(r'\b(X[A-Z]+)(\d+_\d+)\s*=')
        self._decl_pattern = re.compile(r'\bDECL\s+TSg_PCollCD_T\s+(\S+)')
        self._arc_pattern = re.compile(r'\bDECL\s+stArcDat_T\s+')

    def _extract_point_from_line(self, line: str) -> Union[Dict[str, List[float]], None]:
        """Извлекает точку из строки. Возвращает {key: [x, y, z]} или None."""
        line = line.strip()
        coords_match = self._coords_pattern.search(line)
        if not coords_match:
            return None

        name_match = self._name_pattern.search(line)
        if not name_match:
            return None

        point_type = name_match.group(1)  # например, 'XS', 'XW', 'XSE', 'XSS'
        point_num = name_match.group(2)   # например, '2_1'

        point = [
            float(coords_match.group(1)),
            float(coords_match.group(2)),
            float(coords_match.group(3))
        ]

        # Формируем ключ: убираем ведущий 'X', переводим в нижний регистр
        # XS → s, XW → w, XSE → se, XSS → ss
        key = f"{point_type[1:].lower()}{point_num}"

        return {key: point}

    def _find_valid_point_keys_ordered(self, content: str) -> List[Tuple[int, str]]:
        """
        Находит ключи точек с их позициями в файле.
        Возвращает список кортежей (позиция_строки, ключ) в порядке файла.
        """
        lines = content.split('\n')
        
        # Сначала находим все точки с их позициями
        all_points: List[Tuple[int, str]] = []
        for i, line in enumerate(lines):
            point = self._extract_point_from_line(line)
            if point:
                key = list(point.keys())[0]
                all_points.append((i, key))
        
        # Находим индексы строк с DECL TSg_PCollCD_T
        decl_indices = [i for i, line in enumerate(lines) if self._decl_pattern.search(line)]
        
        # Находим индексы строк с DECL stArcDat_T
        arc_indices = [i for i, line in enumerate(lines) if self._arc_pattern.search(line)]
        
        # Собираем валидные ключи с позициями
        valid_points: Set[Tuple[int, str]] = set()
        
        # Для touch: берём две точки перед каждой DECL TSg_PCollCD_T
        for decl_idx in decl_indices:
            points_found: List[Tuple[int, str]] = []
            for i in range(decl_idx - 1, -1, -1):
                for pos, key in all_points:
                    if pos == i:
                        points_found.append((pos, key))
                        if len(points_found) == 2:
                            break
                if len(points_found) == 2:
                    break
            valid_points.update(points_found)
        
        # Для arc: берём одну точку после каждой DECL stArcDat_T
        for arc_idx in arc_indices:
            for i in range(arc_idx + 1, len(lines)):
                for pos, key in all_points:
                    if pos == i:
                        valid_points.add((pos, key))
                        break
                if any(pos == i for pos, _ in valid_points):
                    break
        
        # Сортируем по позиции в файле
        return sorted(valid_points, key=lambda x: x[0])

    def process_dat_content_to_arrays(self, content: str) -> Dict[str, Dict[str, List[List[float]]]]:
        # Находим валидные точки с их позициями (сохраняем порядок файла)
        valid_points = self._find_valid_point_keys_ordered(content)

        # Если не найдено ни одной точки — возвращаем пустой результат
        if not valid_points:
            return {}

        # Создаём множество ключей для быстрой проверки
        valid_keys_set = {key for _, key in valid_points}

        result: Dict[str, Dict[str, List[List[float]]]] = {}
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            point = self._extract_point_from_line(line)
            if not point:
                continue

            key = list(point.keys())[0]
            if key not in valid_keys_set:
                continue

            search_key = key.split('_')[0]

            if search_key not in result:
                result[search_key] = []
            result[search_key].append(point[key])

        return result
