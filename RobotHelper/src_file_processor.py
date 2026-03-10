#!/usr/bin/env python3
import re
from typing import List


class SrcFileProcessor:

    def __init__(self):
        self._def_pattern = re.compile(r'^\s*DEF\s+', re.IGNORECASE)

    def process_src_content(self, content: str) -> str:
        lines = content.split('\n')
        result: List[str] = []
        found_def = False

        for line in lines:
            if not found_def:
                if self._def_pattern.match(line.strip()):
                    found_def = True
                    result.append(line)
                continue

            result.append(line)

        return '\n'.join(result)
