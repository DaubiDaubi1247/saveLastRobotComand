from typing import Dict, List, Optional, Any
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_poller import ROBOTS


class GeneratedPointsRepository:

    def _get_robot_config(self, robot_name: str) -> Optional[Dict[str, Any]]:
        config = ROBOTS.get(robot_name)
        if not config:
            return None
        return {
            "addr": config[0],
            "port": config[1],
            "timeout": config[2] / 1000.0
        }

    def get_robot_points(self, robot_name: str) -> Dict[str, Dict[str, List[List[float]]]]:
        config = self._get_robot_config(robot_name)
        if not config:
            return {}

        connector = RobotConnector(
            addr=config["addr"],
            port=config["port"],
            timeout=config.get("timeout", 3.0)
        )
        try:
            connector.connect()
            connector.authenticate()
            return connector.get_dat_points_by_file(directory="KRC:\\R1\\Program\\generated")
        except Exception:
            return {}
        finally:
            connector.disconnect()
