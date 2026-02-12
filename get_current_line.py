#!/usr/bin/env python3
import argparse
import json
import socket
import sys
from typing import Any, Dict, List, Optional, Union

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


def main() -> None:
    p = argparse.ArgumentParser(
        description="Get current executing program name from KRC4 via KUKAVARPROXY"
    )
    p.add_argument("--host", default="192.168.6.139", help="Robot IP address")
    p.add_argument(
        "--port", type=int, default=3333, help="KUKAVARPROXY port (default 3333)"
    )
    args = p.parse_args()

    try:
        prog = get_program_info(args.host, args.port)
    except Exception as e:
        print("ERROR: communication failed:", e, file=sys.stderr)
        sys.exit(2)

    if prog is None:
        print("Could not read $PRO_IP from robot.")
        sys.exit(1)

    print(prog)


if __name__ == "__main__":
    main()