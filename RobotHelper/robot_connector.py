#!/usr/bin/env python3
import json
import socket
from typing import Any, Dict, List, Optional, Union


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
            self._file_list = r["result"] if isinstance(r["result"], list) else []
        else:
            self._file_list = []

        return self._file_list

    @property
    def file_list(self) -> List[str]:
        return self._file_list

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
