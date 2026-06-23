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

__all__ = ["FreezeSensorValuesBroadcast"]

import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction


class FreezeSensorValuesBroadcast(ModbusPDU):
    """Request freeze of sensor values.

    Parameters
    ----------
    dev_id : `int`
        Broadcast device address. Shall be either
        ELECTROMECHANICAL_BROADCAST_ADDRESS or PNEUMATIC_BROADCAST_ADDRESS.
    communication_counter : `int`
        ILC communication counter. That will be returned in HP_FORCE_AND_STATUS
        or FA_FORCE_AND_STATUS responses.
    """

    function_code = ILCFunction.FREEZE_SENSOR_VALUES
    rtu_frame_size = 1

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, communication_counter: int = 0):
        super().__init__(dev_id=dev_id)

        self.communication_counter = communication_counter

    def encode(self) -> bytes:
        return struct.pack(">B", self.communication_counter)

    def decode(self, data: bytes) -> None:
        self.communication_counter = struct.unpack(">B", data)[0]
