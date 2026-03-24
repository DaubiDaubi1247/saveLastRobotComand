from dataclasses import dataclass
from typing import List, Optional
from influxdb import InfluxDBClient
from config import INFLUX_HOST, INFLUX_PORT, INFLUX_USERNAME, INFLUX_PASSWORD, INFLUX_DATABASE
from utils.logger import logger


@dataclass
class RobotStateDB:
    robot: str


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
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._database = database
        self._client = self._create_client()

    def _create_client(self) -> InfluxDBClient:
        """Создает новое подключение к InfluxDB."""
        return InfluxDBClient(
            host=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            database=self._database
        )

    def _ensure_connection(self) -> None:
        """Проверяет и восстанавливает подключение при необходимости."""
        try:
            self._client.ping()
        except Exception as e:
            logger.warning(f"Потеряно подключение к InfluxDB, переподключение: {e}")
            self._client = self._create_client()

    def get_all_robots_state(self) -> List[RobotStateDB]:
        self._ensure_connection()
        query = """
        SELECT LAST(status) as status
        FROM rob_state
        WHERE status > 1 AND time >= now() - 1m
        GROUP BY robot
        """

        result = self._client.query(query)

        states = []
        for (_, tags), _ in result.items():
            robot_name = tags.get("robot", "")
            if robot_name:
                states.append(RobotStateDB(robot=robot_name))

        return states

    def get_robot_program_info(self, robot: str) -> Optional[RobotProgramDB]:
        self._ensure_connection()
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

        for _, points in result.items():
            point = next(points, None)
            if point:
                program_name = point.get('program_name')
                snr_c = point.get('snr_c')

                if snr_c is not None:
                    try:
                        snr_c = int(snr_c)
                    except (ValueError, TypeError):
                        snr_c = None

                return RobotProgramDB(
                    robot=robot,
                    program_names=program_name,
                    snr_c=snr_c
                )

        return None
