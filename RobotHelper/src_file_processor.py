#!/usr/bin/env python3
import re
from typing import List


class SrcFileProcessor:

    def __init__(self):
        self._fold_start = re.compile(r'^\s*;FOLD\s+(.+?)\s*;%\{PE\}.*$', re.IGNORECASE)
        self._fold_simple = re.compile(r'^\s*;FOLD\s+(.+?)\s*;%\{[Eh]\}.*$', re.IGNORECASE)
        self._fold_end = re.compile(r'^\s*;ENDFOLD', re.IGNORECASE)
        self._function_call = re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*\(')
        self._sync_pattern = re.compile(r'^\s*SYNC\s+', re.IGNORECASE)
        self._touchsense_pattern = re.compile(r'TouchSense', re.IGNORECASE)
        self._move_command = re.compile(r'^\s*(PTP|LIN|CIRC)\s+', re.IGNORECASE)
        self._ts_command = re.compile(r'^\s*TS_\w+\s*\(')
        self._bas_command = re.compile(r'^\s*BAS\s*\(')
        self._set_cd_command = re.compile(r'^\s*SET_CD_PARAMS\s*\(')
        self._arc_command = re.compile(r'^\s*ArcMainNG\s*\(')

    def process_src_content(self, content: str) -> str:
        lines = content.split('\n')
        result: List[str] = []
        in_fold = False
        fold_content_saved = False
        is_touchsense_fold = False

        for line in lines:
            stripped = line.strip()

            if 'Parameters TouchSense' in stripped:
                continue

            if self._bas_command.match(stripped) or self._set_cd_command.match(stripped):
                continue

            if self._ts_command.match(stripped):
                continue

            if self._arc_command.match(stripped):
                continue

            fold_start_match = self._fold_start.match(stripped)
            if fold_start_match:
                in_fold = True
                fold_content_saved = False
                fold_name = fold_start_match.group(1).strip()
                is_touchsense_fold = bool(self._touchsense_pattern.search(fold_name))

                if is_touchsense_fold:
                    result.append(fold_name)
                    result.append("")
                else:
                    sync_match = self._sync_pattern.search(fold_name)
                    if sync_match:
                        sync_part = fold_name[sync_match.start():]
                        result.append(sync_part)
                        result.append("")
                continue

            fold_simple_match = self._fold_simple.match(stripped)
            if fold_simple_match:
                fold_name = fold_simple_match.group(1).strip()
                is_touchsense_fold = bool(self._touchsense_pattern.search(fold_name))
                if is_touchsense_fold:
                    result.append(fold_name)
                    result.append("")
                continue

            if in_fold and self._fold_end.match(stripped):
                in_fold = False
                if not is_touchsense_fold:
                    result.append("")
                is_touchsense_fold = False
                continue

            if in_fold and not fold_content_saved:
                if is_touchsense_fold:
                    continue
                if self._move_command.match(stripped):
                    result.append(line)
                    fold_content_saved = True
                continue

            if self._function_call.match(stripped):
                result.append(line)

        return '\n'.join(result)
