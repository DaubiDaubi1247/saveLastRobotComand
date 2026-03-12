from dataclasses import dataclass
from typing import List, Optional
from influxdb import InfluxDBClient
from config import INFLUX_HOST, INFLUX_PORT, INFLUX_USERNAME, INFLUX_PASSWORD, INFLUX_DATABASE


@dataclass
class RobotStateDB:
    robot: str
    status: Optional[int] = None
    time: Optional[str] = None


@dataclass
class RobotProgramDB:
    robot: str
    program_names: Optional[str] = None
    snr_c: Optional[int] = None


class RobotStateRepository:

    def __init__(
        self,
        host: str = INFLUX_HOST,
        port: int = INFLUX_PORT,
        username: str = INFLUX_USERNAME,
        password: str = INFLUX_PASSWORD,
        database: str = INFLUX_DATABASE
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
        WHERE status > 1 AND time >= now() - 1m
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

    def get_robot_program_info(self, robot: str) -> Optional[RobotProgramDB]:
        query = f"""
        SELECT program_name, snr_c
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
                program_name = point.get('program_name')
                snr_c = point.get('snr_c')

                if not program_name:
                    program_name = None
                if snr_c is not None:
                    try:
                        snr_c = int(snr_c)
                    except (ValueError, TypeError):
                        snr_c = None
                else:
                    snr_c = None

                return RobotProgramDB(
                    robot=robot,
                    program_names=program_name,
                    snr_c=snr_c
                )

        return None
