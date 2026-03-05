#!/usr/bin/env python3
import re
import json
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

    def process_dat_content(self, content: str) -> str:
        lines = content.split('\n')
        filtered_lines: List[str] = []

        for line in lines:
            line = line.strip()
            if self._pattern.search(line):
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def process_dat_content_to_arrays(self, content: str) -> Dict[str, List[List[float]]]:
        result: Dict[str, List[List[float]]] = {"s": [], "w": []}
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            xs_match = re.search(r'\bXS[A-Z0-9_]*\s*=', line)
            xw_match = re.search(r'\bXW[A-Z0-9_]*\s*=', line)

            coords_match = self._coords_pattern.search(line)
            if not coords_match:
                continue

            point = [
                float(coords_match.group(1)),
                float(coords_match.group(2)),
                float(coords_match.group(3))
            ]

            if xs_match:
                result["s"].append(point)
            elif xw_match:
                result["w"].append(point)

        return result

    def should_process(self, file_name: str) -> bool:
        return file_name.endswith('.dat')
