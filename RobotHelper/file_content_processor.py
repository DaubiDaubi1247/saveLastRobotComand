#!/usr/bin/env python3
import re
from typing import List


class FileContentProcessor:

    def __init__(self):
        self._pattern = re.compile(
            r'\b(?:XS|XW)[A-Z0-9_]*\s*=\s*\{[^}]+\}',
            re.MULTILINE
        )

    def process_dat_content(self, content: str) -> str:
        lines = content.split('\n')
        filtered_lines: List[str] = []

        for line in lines:
            line = line.strip()
            if self._pattern.search(line):
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def should_process(self, file_name: str) -> bool:
        return file_name.endswith('.dat')
