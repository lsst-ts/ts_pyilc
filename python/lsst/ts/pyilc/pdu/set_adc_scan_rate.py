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

__all__ = ["ADCScanRate", "SetADCScanRate"]

import struct
from enum import IntEnum

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction


class ADCScanRate(IntEnum):
    RATE_50 = 0
    RATE_60 = 1
    RATE_100 = 2
    RATE_120 = 3
    RATE_200 = 4
    RATE_240 = 5
    RATE_300 = 6
    RATE_400 = 7
    RATE_480 = 8
    RATE_600 = 9
    RATE_1200 = 10
    RATE_2400 = 11
    RATE_4800 = 12
    NO_CHANGE = 0xFF


class SetADCScanRate(ModbusPDU):
    function_code = ILCFunction.SET_ADC_SCANRATE
    rtu_frame_size = 1

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, scan_rate: ADCScanRate = ADCScanRate.NO_CHANGE):
        super().__init__(dev_id=dev_id)
        self.scan_rate = scan_rate

    def encode(self) -> bytes:
        return struct.pack(">B", self.scan_rate)

    def decode(self, data: bytes) -> None:
        self.scan_rate = ADCScanRate(data[0])
