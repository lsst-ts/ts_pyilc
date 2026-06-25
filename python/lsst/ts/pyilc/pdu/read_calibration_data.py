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

__all__ = ["ReadCalibrationDataRequest", "ReadCalibrationDataResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ReadCalibrationDataRequest(ILCRequest):
    function_code = ILCFunction.READ_CALIBRATION_DATA


class ReadCalibrationDataResponse(ModbusPDU):
    """Reads calibration data."""

    function_code = ILCFunction.READ_CALIBRATION_DATA
    rtu_frame_size = 96

    NUM_CALIBRATION = 4

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.main_adc_calibration = [m.nan] * self.NUM_CALIBRATION
        self.main_sensor_offset = [m.nan] * self.NUM_CALIBRATION
        self.main_sensor_sensitivity = [m.nan] * self.NUM_CALIBRATION

        self.backup_adc_calibration = [m.nan] * self.NUM_CALIBRATION
        self.backup_sensor_offset = [m.nan] * self.NUM_CALIBRATION
        self.backup_sensor_sensitivity = [m.nan] * self.NUM_CALIBRATION

    def encode(self) -> bytes:
        return struct.pack(
            ">24f",
            *self.main_adc_calibration,
            *self.main_sensor_offset,
            *self.main_sensor_sensitivity,
            *self.backup_adc_calibration,
            *self.backup_sensor_offset,
            *self.backup_sensor_sensitivity,
        )

    def decode(self, data: bytes) -> None:
        def __unpack_array(data: bytes, serie: int) -> list[float]:
            return list(
                struct.unpack(
                    ">4f", data[serie * self.NUM_CALIBRATION * 4 : (serie + 1) * self.NUM_CALIBRATION * 4]
                )
            )

        self.main_adc_calibration = __unpack_array(data, 0)
        self.main_sensor_offset = __unpack_array(data, 1)
        self.main_sensor_sensitivity = __unpack_array(data, 2)

        self.backup_adc_calibration = __unpack_array(data, 3)
        self.backup_sensor_offset = __unpack_array(data, 4)
        self.backup_sensor_sensitivity = __unpack_array(data, 5)
