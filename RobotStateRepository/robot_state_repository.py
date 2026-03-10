from dataclasses import dataclass
from typing import List, Optional
from influxdb import InfluxDBClient


@dataclass
class RobotStateDB:
    robot: str
    program_names: Optional[str] = None
    snr_c: Optional[int] = None


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
        SELECT program_names, snr_c
        FROM program_info
        WHERE robot = '{robot}' AND time >= now() - 1m
        ORDER BY time DESC
        LIMIT 1
        """

        result = self._client.query(query)

        if not result:
            return None

        for (measurement, tags), points in result.items():
            point = next(points, None)
            if point:
                return RobotStateDB(
                    robot=robot,
                    program_names=point.get('program_names'),
                    snr_c=point.get('snr_c')
                )

        return None

    def get_all_robots_state(self) -> List[RobotStateDB]:
        query = """
        SELECT program_names, snr_c
        FROM program_info
        WHERE time >= now() - 1m
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
                    program_names=point.get('program_names'),
                    snr_c=point.get('snr_c')
                ))

        return states

    def get_robot_program_info(self, robot: str) -> Optional[RobotStateDB]:
        query = f"""
        SELECT program_names, snr_c
        FROM program_info
        WHERE robot = '{robot}' AND time >= now() - 1m
        ORDER BY time DESC
        LIMIT 1
        """

        result = self._client.query(query)

        if not result:
            return None

        for (measurement, tags), points in result.items():
            point = next(points, None)
            if point:
                return RobotStateDB(
                    robot=robot,
                    program_names=point.get('program_names'),
                    snr_c=point.get('snr_c')
                )

        return None
