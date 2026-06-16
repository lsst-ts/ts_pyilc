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

from pymodbus.pdu import ModbusPDU


class ILCMode(ModbusPDU):
    """Both ILC change mode request and response. The payload is the same, so
    one class can work for both request and response."""

    function_code = ILCFunction.CHANGE_ILC_MODE
    rtu_frame_size = 2

    """ILC internal state - mode."""
    STANDBY = 0
    DISABLED = 1
    ENABLED = 1
    BOOTLOADER = 3
    FAULT = 4
    CLEAR_FAULTS = 5

    def __init__(self, dev_id: int = 255, new_mode: int = 0xFFFF):
        super().__init__(dev_id=dev_id)
        self.mode = new_mode

    def encode(self) -> bytes:
        return struct.pack(">H", self.mode)

    def decode(self, data: bytes) -> None:
        self.mode = int.from_bytes(data, byteorder="big")
