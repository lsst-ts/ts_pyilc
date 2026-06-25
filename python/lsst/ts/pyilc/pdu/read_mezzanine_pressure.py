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

__all__ = ["ReadMezzaninePressureRequest", "ReadMezzaninePressureResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ReadMezzaninePressureRequest(ILCRequest):
    function_code = ILCFunction.READ_MEZZANINE_PRESSURE


class ReadMezzaninePressureResponse(ModbusPDU):
    """Reads pressure reported by mezzanine board."""

    function_code = ILCFunction.READ_MEZZANINE_PRESSURE
    rtu_frame_size = 16

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.axial_push = m.nan
        self.axial_pull = m.nan
        self.lateral_pull = m.nan
        self.lateral_push = m.nan

    def encode(self) -> bytes:
        return struct.pack(
            ">4f",
            self.axial_push,
            self.axial_pull,
            self.lateral_pull,
            self.lateral_push,
        )

    def decode(self, data: bytes) -> None:
        (self.axial_push, self.axial_pull, self.lateral_pull, self.lateral_push) = struct.unpack(">4f", data)
