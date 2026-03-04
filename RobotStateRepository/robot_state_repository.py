from dataclasses import dataclass
from typing import List, Optional
from influxdb import InfluxDBClient

# Typing is not used because there is no library for types

@dataclass
class RobotStateDB:
    robot: str
    status: Optional[int] = None
    time: Optional[str] = None


class RobotStateRepository:

    def __init__(
        self,
        host: str = '192.168.22.11',
        port: int = 8086,
        username: str = 'user',
        password: str = 'pass',
        database: str = 'influx'
    ):
        self._client = InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )

    def get_robot_state(self, robot: str) -> Optional[RobotStateDB]:
        query = f"""
        SELECT LAST(status) as status, time
        FROM rob_state
        WHERE robot = '{robot}' AND status != 0 AND time >= now() - 1m
        """

        result = self._client.query(query)

        if not result:
            return None

        for (measurement, tags), points in result.items():
            point = next(points, None)
            if point:
                return RobotStateDB(
                    robot=robot,
                    status=point.get('last'),
                    time=point.get('time')
                )

        return None

    def get_all_robots_state(self) -> List[RobotStateDB]:
        query = """
        SELECT LAST(status) as status, time
        FROM rob_state
        WHERE status != 0 AND time >= now() - 1m
        GROUP BY robot
        """

        result = self._client.query(query)

        states = []
        for (measurement, tags), points in result.items():
            robot_name = tags.get("robot", "")
            point = next(points, None)
            if point:
                states.append(RobotStateDB(
                    robot=robot_name,
                    status=point.get('last'),
                    time=point.get('time')
                ))

        return states
