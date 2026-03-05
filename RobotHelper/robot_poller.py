#!/usr/bin/env python3
import asyncio
import json
import socket
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from telegraf.client import TelegrafClient
from .robot_connector import request

POLL_INTERVAL = 15

TELEGRAF_HOST = "192.168.22.11"
TELEGRAF_PORT = 8092

ROBOTS: Dict[str, Tuple[str, int, int, str]] = {
    'W8R1': ('10.1.0.82', 3333, 2000, 'W8R1'),
    'W8R2': ('10.1.0.84', 3333, 2000, 'W8R2'),
    'W8R3': ('10.1.0.86', 3333, 2000, 'W8R3'),
    'W8R4': ('10.1.0.88', 3333, 2000, 'W8R4'),
    'W1R1': ('10.1.0.14', 3333, 2000, 'W1R1'),
    'W1R2': ('10.1.0.16', 3333, 2000, 'W1R2'),
    'W2R1': ('10.1.0.44', 3333, 2000, 'W2R1'),
    'W2R2': ('10.1.0.46', 3333, 2000, 'W2R2'),
    'W1x4R1': ('10.1.0.32', 4444, 2000, 'W1x4R1'),
    'W1x4R2': ('10.1.0.34', 3333, 2000, 'W1x4R2'),
    'W1x4R3': ('10.1.0.36', 4444, 2000, 'W1x4R3'),
    'W1x4R4': ('10.1.0.38', 3333, 2000, 'W1x4R4'),
    'W8R5': ('10.1.0.117', 3333, 2000, 'W8R5'),
    'W7R1': ('10.1.0.71', 3333, 2000, 'W7R1'),
    'W1R7': ('10.1.0.18', 3333, 2000, 'W1R7'),
    'W2R6': ('10.1.0.26', 3333, 2000, 'W2R6')
}


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


class RobotPoller:

    def __init__(self, host: str = TELEGRAF_HOST, port: int = TELEGRAF_PORT):
        self._tg_client = TelegrafClient(host=host, port=port)
        self._robots = ROBOTS

    def _send_to_telegraf(self, info: ProgramInfo, robot_tag: str) -> None:
        data = {
            "snr_c_trl": info.snr_c_trl if info.snr_c_trl is not None else 0,
            "program_name": info.name_c_trl if info.name_c_trl is not None else None,
        }
        self._tg_client.metric("program_info", data, tags={"robot": robot_tag})

    def _poll_robot(self, key: str, config: Tuple[str, int, int, str]) -> None:
        try:
            info = get_program_info(config[0], int(config[1]))
            self._send_to_telegraf(info, config[3])
        except Exception as e:
            print(f"{key}: {e}")

    def poll_all(self) -> None:
        for key, config in self._robots.items():
            self._poll_robot(key, config)

    async def run(self) -> None:
        while True:
            await asyncio.to_thread(self.poll_all)
            await asyncio.sleep(POLL_INTERVAL)


async def poll_robots() -> None:
    await RobotPoller().run()
