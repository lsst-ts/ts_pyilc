# This file is part of ts_pyilc.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = [
    "ReadMonitorSensorsRequest",
    "ReadMonitorTemperatureSensorsResponse",
    "ReadMonitorDisplacementSensorsResponse",
    "ReadMonitorInclinometerSensorsResponse",
]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ReadMonitorSensorsRequest(ILCRequest):
    function_code = ILCFunction.READ_MONITOR_SENSORS


class ReadMonitorTemperatureSensorsResponse(ModbusPDU):
    function_code = ILCFunction.READ_MONITOR_SENSORS
    rtu_frame_size = 16

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.temperature = [m.nan] * 4

    def encode(self) -> bytes:
        return struct.pack(">4f", *self.temperature)

    def decode(self, data: bytes) -> None:
        self.temperature = list(struct.unpack(">4f", data))


class ReadMonitorDisplacementSensorsResponse(ModbusPDU):
    function_code = ILCFunction.READ_MONITOR_SENSORS
    rtu_frame_size = 48

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.displacement = [m.nan] * 12

    def encode(self) -> bytes:
        return struct.pack(">12f", *self.displacement)

    def decode(self, data: bytes) -> None:
        self.displacement = list(struct.unpack(">12f", data))


class ReadMonitorInclinometerSensorsResponse(ModbusPDU):
    function_code = ILCFunction.READ_MONITOR_SENSORS
    rtu_frame_size = 4

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.elevation_angle = m.nan

    def encode(self) -> bytes:
        return struct.pack(">f", self.elevation_angle)

    def decode(self, data: bytes) -> None:
        self.elevation_angle = list(struct.unpack(">f", data))[0]
