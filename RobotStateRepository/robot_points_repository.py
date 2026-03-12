from typing import Any, Dict, List, Optional
from RobotHelper.robot_connector import RobotConnector
from RobotHelper.robot_poller import ROBOTS


class RobotPointsRepository:

    def _get_robot_config(self, robot_name: str) -> Optional[Dict[str, Any]]:
        config = ROBOTS.get(robot_name)
        if not config:
            return None
        return {
            "addr": config[0],
            "port": config[1],
            "timeout": config[2] / 1000.0
        }

    def get_robot_points(self, robot_name: str) -> Dict[str, List[List[float]]]:
        config = self._get_robot_config(robot_name)
        if not config:
            return {"s": [], "w": []}

        connector = RobotConnector(
            addr=config["addr"],
            port=config["port"],
            timeout=config.get("timeout", 3.0)
        )
        try:
            connector.connect()
            connector.authenticate()
            return connector.get_dat_points()
        except Exception:
            return {"s": [], "w": []}
        finally:
            connector.disconnect()
