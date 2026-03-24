#!/usr/bin/env python3
import asyncio
import json
import socket
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from telegraf.client import TelegrafClient
from .robot_connector import request
from config import POLL_INTERVAL, TELEGRAF_HOST, TELEGRAF_PORT, ROBOTS
from utils.logger import logger


@dataclass
class ProgramInfo:
    name_c: Optional[str] = None
    snr_c: Optional[int] = None


def parse_pro_ip_result(result_str: str) -> ProgramInfo:
    s = result_str.strip()
    if s.startswith("{PRO_IP:") and s.endswith("}"):
        s = s[8:-1].strip()

    name_c_match = re.search(r'NAME_C\[\]\s*"([^"]*)"', s)
    snr_c_match = re.search(r'SNR_C\s+(\d+)', s)

    return ProgramInfo(
        name_c=name_c_match.group(1) if name_c_match else None,
        snr_c=int(snr_c_match.group(1)) if snr_c_match else None,
    )


def get_program_info(addr: str, port: int, timeout: float = 3.0) -> ProgramInfo:
    msg = json.dumps({"method": "Var_ShowVar", "params": ["$PRO_IP"], "id": 1}) + "\n"
    with socket.create_connection((addr, port), timeout) as client:
        r = request(msg, client, timeout)

    result_str = r.get("result", str(r)) if isinstance(r, dict) else str(r)
    return parse_pro_ip_result(result_str)

class RobotPoller:

    def __init__(self, host: str = TELEGRAF_HOST, port: int = TELEGRAF_PORT):
        self._tg_client = TelegrafClient(host=host, port=port)
        self._robots = ROBOTS

    def _send_to_telegraf(self, info: ProgramInfo, robot_tag: str) -> None:
        data = {
            "snr_c": info.snr_c if info.snr_c is not None else 0,
            "program_name": info.name_c if info.name_c is not None else None,
        }
        self._tg_client.metric("program_info", data, tags={"robot": robot_tag})

    def _poll_robot(self, key: str, config: Tuple[str, int, int, str]) -> None:
        try:
            info = get_program_info(config[0], config[1])
            self._send_to_telegraf(info, config[3])
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"{key}: {e}")

    def poll_all(self) -> None:
        for key, config in self._robots.items():
            self._poll_robot(key, config)

    async def run(self) -> None:
        while True:
            await asyncio.to_thread(self.poll_all)
            await asyncio.sleep(POLL_INTERVAL)


async def poll_robots() -> None:
    await RobotPoller().run()
