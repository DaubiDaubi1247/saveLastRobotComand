#!/usr/bin/env python3
import json
import socket
import time
import os
import re
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

POLL_INTERVAL = 1.0
OUTFILE = "last_program.txt"
HOST = "192.168.6.139"
PORT = 3333

@dataclass
class ProgramInfo:
    name: Optional[str] = None
    snr: Optional[int] = None
    name_c: Optional[str] = None
    snr_c: Optional[int] = None
    name_c_trl: Optional[str] = None
    snr_c_trl: Optional[int] = None
    i_executed: Optional[bool] = None
    p_arrived: Optional[int] = None


def parse_pro_ip_result(result_str: str) -> ProgramInfo:
    s = result_str.strip()
    if s.startswith("{PRO_IP:") and s.endswith("}"):
        s = s[8:-1].strip()
    
    name_match = re.search(r'NAME\[\]\s*"([^"]*)"', s)
    snr_match = re.search(r'SNR\s+(\d+)', s)
    name_c_match = re.search(r'NAME_C\[\]\s*"([^"]*)"', s)
    snr_c_match = re.search(r'SNR_C\s+(\d+)', s)
    name_c_trl_match = re.search(r'NAME_C_TRL\[\]\s*"([^"]*)"', s)
    snr_c_trl_match = re.search(r'SNR_C_TRL\s+(\d+)', s)
    i_executed_match = re.search(r'I_EXECUTED\s+(TRUE|FALSE)', s, re.IGNORECASE)
    p_arrived_match = re.search(r'P_ARRIVED\s+(\d+)', s)
    
    return ProgramInfo(
        name=name_match.group(1) if name_match else None,
        snr=int(snr_match.group(1)) if snr_match else None,
        name_c=name_c_match.group(1) if name_c_match else None,
        snr_c=int(snr_c_match.group(1)) if snr_c_match else None,
        name_c_trl=name_c_trl_match.group(1) if name_c_trl_match else None,
        snr_c_trl=int(snr_c_trl_match.group(1)) if snr_c_trl_match else None,
        i_executed=i_executed_match.group(1).upper() == "TRUE" if i_executed_match else None,
        p_arrived=int(p_arrived_match.group(1)) if p_arrived_match else None,
    )

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


def get_program_info(addr: str, port: int, timeout: float = 3.0) -> ProgramInfo:
    msg = json.dumps({"method": "Var_ShowVar", "params": ["$PRO_IP"], "id": 1}) + "\n"
    with socket.create_connection((addr, port), timeout) as client:
        r = request(msg, client, timeout)

    if isinstance(r, dict) and "result" in r:
        result_str = r["result"]
    elif isinstance(r, str):
        result_str = r
    else:
        result_str = str(r)
    
    return parse_pro_ip_result(result_str)

def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    try:
        while True:
            try:
                write_atomic(Path(OUTFILE), json.dumps(asdict(get_program_info(HOST, PORT)), indent=2, ensure_ascii=False))
            except Exception as e:
                print(e)
            time.sleep(max(0.1, float(POLL_INTERVAL)))
    except KeyboardInterrupt:
        print("Interrupted, exiting.")
        return


if __name__ == "__main__":
    main()