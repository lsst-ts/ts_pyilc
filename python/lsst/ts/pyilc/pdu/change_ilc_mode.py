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

from .utils import ILCFunction

__all__ = ["ILCMode"]

import struct
from enum import IntEnum

from pymodbus.pdu import ModbusPDU


class ILCMode(IntEnum):
    # ILC internal state - mode
    STANDBY = 0
    DISABLED = 1
    ENABLED = 2
    BOOTLOADER = 3
    FAULT = 4
    CLEAR_FAULTS = 5


class ChangeILCMode(ModbusPDU):
    """Both ILC change mode request and response. The payload is the same, so
    one class can work for both request and response.

    Parameters
    ----------

    dev_id : `int`
        ILC address.
    new_mode : `int`, optional
        Desired mode. Construct command to transition to that mode if
        current_mode is not provided. Note that the default, 0xFFFF, is a mode
        query - function will return current system state.
    current_mode : `int`, optional
        If provided, construct ILCMode query to reach the given state.
    """

    function_code = ILCFunction.CHANGE_ILC_MODE
    rtu_frame_size = 2

    def __init__(self, dev_id: int = 255, new_mode: int = 0xFFFF, current_mode: int | None = None):
        super().__init__(dev_id=dev_id)
        if current_mode is not None:
            if new_mode == ILCMode.FAULT:
                self.mode = new_mode
            elif new_mode == current_mode:
                self.mode = 0xFFFF
            elif current_mode == ILCMode.FAULT:
                self.mode = ILCMode.CLEAR_FAULTS
            elif current_mode == ILCMode.BOOTLOADER:
                self.mode = ILCMode.STANDBY
            elif new_mode == ILCMode.BOOTLOADER:
                if current_mode == ILCMode.STANDBY:
                    self.mode = ILCMode.BOOTLOADER
                else:
                    self.mode = current_mode - 1
            elif current_mode in (ILCMode.STANDBY, ILCMode.DISABLED, ILCMode.ENABLED):
                self.mode = current_mode + (1 if new_mode > current_mode else -1)
            else:
                self.mode = 0xFFFF
        else:
            self.mode = new_mode

    def encode(self) -> bytes:
        return struct.pack(">H", self.mode)

    def decode(self, data: bytes) -> None:
        self.mode = struct.unpack(">H", data)[0]
