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

__all__ = ["SetReheaterGainsRequest", "SetReheaterGainsResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCResponse


class SetReheaterGainsRequest(ModbusPDU):
    """Sets thermal (FCU) re-heater PID gains.

    Parameters
    ----------
    dev_id : `int`
        ILC address.
    p : `float`
        Re-heater proportional gain.
    i : `float`
        Re-heater integral gain.
    """

    function_code = ILCFunction.SET_REHEATER_GAINS
    rtu_frame_size = 8

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, p: float = m.nan, i: float = m.nan):
        super().__init__(dev_id=dev_id)

        self.p = p
        self.i = i

    def encode(self) -> bytes:
        return struct.pack(">ff", self.p, self.i)

    def decode(self, data: bytes) -> None:
        (self.p, self.i) = struct.unpack(">ff", data)


class SetReheaterGainsResponse(ILCResponse):
    function_code = ILCFunction.SET_REHEATER_GAINS
