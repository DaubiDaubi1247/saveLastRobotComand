#!/usr/bin/env python3
import re
from typing import Dict, List


class FileContentProcessor:

    def __init__(self):
        self._pattern = re.compile(
            r'\b(?:XS|XW)[A-Z0-9_]*\s*=\s*\{[^}]+\}',
            re.MULTILINE
        )
        self._coords_pattern = re.compile(
            r'X\s*(-?\d+\.?\d*),\s*Y\s*(-?\d+\.?\d*),\s*Z\s*(-?\d+\.?\d*)'
        )
        self._name_pattern = re.compile(r'\b(X[SW])(\d+)_\d+\s*=')

    def process_dat_content(self, content: str) -> str:
        lines = content.split('\n')
        filtered_lines: List[str] = []

        for line in lines:
            line = line.strip()
            if self._pattern.search(line):
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def process_dat_content_to_arrays(self, content: str) -> Dict[str, Dict[str, List[List[float]]]]:
        result: Dict[str, Dict[str, List[List[float]]]] = {}
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            coords_match = self._coords_pattern.search(line)
            if not coords_match:
                continue

            name_match = self._name_pattern.search(line)
            if not name_match:
                continue

            point_type = name_match.group(1)
            point_num = name_match.group(2)

            point = [
                float(coords_match.group(1)),
                float(coords_match.group(2)),
                float(coords_match.group(3))
            ]

            if point_type == "XS":
                key = f"s{point_num}"
            else:
                key = f"w{point_num}"

            if key not in result:
                result[key] = []
            result[key].append(point)

        return result

    def should_process(self, file_name: str) -> bool:
        return file_name.endswith('.dat')
