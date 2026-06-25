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

__all__ = ["ForceActuatorReadBoosterValveDCAGainsRequest", "ForceActuatorReadBoosterValveDCAGainsResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ForceActuatorReadBoosterValveDCAGainsRequest(ILCRequest):
    function_code = ILCFunction.FA_READ_BOOSTER_VALVE_DCA_GAINS


class ForceActuatorReadBoosterValveDCAGainsResponse(ModbusPDU):
    function_code = ILCFunction.FA_READ_BOOSTER_VALVE_DCA_GAINS
    rtu_frame_size = 8

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.axial_gain = m.nan
        self.lateral_gain = m.nan

    def encode(self) -> bytes:
        return struct.pack(">ff", self.axial_gain, self.lateral_gain)

    def decode(self, data: bytes) -> None:
        (self.axial_gain, self.lateral_gain) = struct.unpack(">ff", data)
