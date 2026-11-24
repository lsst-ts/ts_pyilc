# This file is part of ts_pyilc.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

__all__ = ["ReadMezzanineLVDTRequest", "ReadMezzanineLVDTResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest, pdu_stringify


class ReadMezzanineLVDTRequest(ILCRequest):
    function_code = ILCFunction.HM_READ_MEZZANINE_LVDT


@pdu_stringify(lvdt_1=".6f", lvdt_2=".6f")
class ReadMezzanineLVDTResponse(ModbusPDU):
    function_code = ILCFunction.HM_READ_MEZZANINE_LVDT

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.lvdt_1 = m.nan
        self.lvdt_2 = m.nan

    def x_encode(self) -> bytes:
        return struct.pack(">ff", self.lvdt_1, self.lvdt_2)

    def x_decode(self, data: bytes) -> None:
        (self.lvdt_1, self.lvdt_2) = struct.unpack(">ff", data)

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        return 12
