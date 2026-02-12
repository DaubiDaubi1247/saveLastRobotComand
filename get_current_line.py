#!/usr/bin/env python3
import json
import socket
import time
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

POLL_INTERVAL = 5.0  # seconds between polls when running continuously
OUTFILE = "last_program.txt"  # file to write last program name to
HOST = "192.168.6.139"
PORT = 3333

def request(command: str, client: socket.socket, timeout: float = 3.0) -> Union[Dict[str, Any], List[Any], str]:
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


def get_program_info(addr: str, port: int, timeout: float = 3.0) -> Optional[str]:
    msg = json.dumps({"method": "Var_ShowVar", "params": ["$PRO_IP"], "id": 1}) + "\n"
    with socket.create_connection((addr, port), timeout) as client:
        r = request(msg, client, timeout)

    if isinstance(r, (list, dict)):
        sval = json.dumps(r, ensure_ascii=False)
    else:
        sval = str(r)
    sval = sval.strip()
    return sval

def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    outpath = Path(OUTFILE)

    try:
        while True:
            try:
                prog = get_program_info(HOST, PORT)
            except Exception as e:
                write_atomic(outpath, f"ERROR: {e}\n")
            else:
                write_atomic(outpath, (prog or "").strip())
            time.sleep(max(0.1, float(POLL_INTERVAL)))
    except KeyboardInterrupt:
        print("Interrupted, exiting.")
        return


if __name__ == "__main__":
    main()