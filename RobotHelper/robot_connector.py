#!/usr/bin/env python3
import json
import socket
import os
from typing import Any, Dict, List, Optional, Union
from .file_content_processor import FileContentProcessor
from .src_file_processor import SrcFileProcessor


def request(command: str, client: socket.socket, timeout: float = 3.0) -> Union[Dict[str, Any], str]:
    if not command.endswith("\n"):
        command += "\n"
    client.settimeout(timeout)
    client.send(command.encode())
    resp = bytearray()
    while True:
        chunk = client.recv(4096)
        if not chunk:
            break
        resp.extend(chunk)
        if resp.endswith(b"\n"):
            break
    text = resp.decode("utf-8", errors="ignore").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class RobotConnector:

    def __init__(self, addr: str, port: int, timeout: float = 3.0):
        self._addr = addr
        self._port = port
        self._timeout = timeout
        self._client: Optional[socket.socket] = None
        self._file_list: List[str] = []
        self._processor = FileContentProcessor()
        self._src_processor = SrcFileProcessor()

    def connect(self) -> None:
        self._client = socket.create_connection((self._addr, self._port), self._timeout)

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _send_request(self, command: str) -> Union[Dict[str, Any], str]:
        if self._client is None:
            raise RuntimeError("Not connected to robot")
        return request(command, self._client, self._timeout)

    def authenticate(self, key: str = "My_example_KEY") -> bool:
        msg = json.dumps({"method": "auth", "params": [key], "id": 1}) + "\n"
        r = self._send_request(msg)
        return isinstance(r, dict) and r.get("result") is True

    def get_file_list(self, directory: str = "KRC:\\R1\\Program\\sasha_test") -> List[str]:
        msg = json.dumps({
            "method": "File_NameList",
            "params": [directory, 511, 127],
            "id": 1
        }) + "\n"
        r = self._send_request(msg)

        if isinstance(r, dict) and "result" in r:
            result = r["result"]
            if isinstance(result, dict):
                self._file_list = list(result.keys())
            elif isinstance(result, list):
                self._file_list = result
            else:
                self._file_list = []
        else:
            self._file_list = []

        return self._file_list

    @property
    def file_list(self) -> List[str]:
        return self._file_list

    def _get_dat_files(self) -> List[str]:
        return [f for f in self._file_list if f.endswith('.dat')]

    def _get_src_files(self) -> List[str]:
        return [f for f in self._file_list if f.endswith('.src')]

    def _copy_file_to_mem(self, file_path: str) -> Optional[str]:
        msg = json.dumps({
            "method": "File_CopyFile2Mem",
            "params": [file_path],
            "id": 1
        }) + "\n"
        r = self._send_request(msg)
        if isinstance(r, dict) and "result" in r:
            return r["result"]
        return None

    def copy_files_to_local(self, directory: str = "KRC:\\R1\\Program\\work", output_dir: str = "robot_files", robot_name: Optional[str] = None, process_src: bool = True) -> List[str]:
        if not self._file_list:
            self.get_file_list(directory)

        if robot_name:
            output_dir = os.path.join(output_dir, robot_name)
        
        os.makedirs(output_dir, exist_ok=True)
        saved_files: List[str] = []
        src_files = self._get_src_files()
        for file_name in src_files:
            file_path = f"{directory}\\{file_name}"
            content = self._copy_file_to_mem(file_path)
            if content is not None:
                if process_src:
                    content = self._src_processor.process_src_content(content)
                local_path = os.path.join(output_dir, file_name)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(content)
                saved_files.append(file_name)

        return saved_files

    def get_dat_points(self, directory: str = "KRC:\\R1\\Program\\work") -> Dict[str, Dict[str, List[List[float]]]]:
        if not self._file_list:
            self.get_file_list(directory)

        dat_files = self._get_dat_files()
        result: Dict[str, Dict[str, List[List[float]]]] = {}

        for file_name in dat_files:
            file_path = f"{directory}\\{file_name}"
            content = self._copy_file_to_mem(file_path)
            if content is not None:
                points = self._processor.process_dat_content_to_arrays(content)
                for key, value in points.items():
                    if key not in result:
                        result[key] = []
                    result[key].extend(value)

        return result

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self):
        self.disconnect()

# r = RobotConnector(addr="10.1.0.82", port=3333)
# r.connect()
# r.authenticate()
# r.copy_files_to_local()