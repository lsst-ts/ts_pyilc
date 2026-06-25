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

__all__ = ["ReadMezzanineStatusRequest", "ReadMezzanineStatusResponse"]

import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ReadMezzanineStatusRequest(ILCRequest):
    function_code = ILCFunction.READ_MEZZANINE_STATUS


class ReadMezzanineStatusResponse(ModbusPDU):
    function_code = ILCFunction.READ_MEZZANINE_STATUS
    rtu_frame_size = 2

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.status: int = 0

    def encode(self) -> bytes:
        return struct.pack(">H", self.status)

    def decode(self, data: bytes) -> None:
        self.status = struct.unpack(">H", data)[0]

    def status_bits(self) -> dict[str, str]:
        def __ok_fault(status: int) -> str:
            return "OK" if status else "Fault"

        return {
            "Outputs Enabled / S1A 1 Interface": __ok_fault(self.status & 0x0001),
            "Power fail / S1A 1 LVDT": __ok_fault(self.status & 0x0002),
            "Current AMP A / S1A 2 Interface": __ok_fault(self.status & 0x0004),
            "Current AMP B / S1A 2 LVDT": __ok_fault(self.status & 0x0008),
            "UID Device": __ok_fault(self.status & 0x0010),
            # 0x0020 is reserved
            "Main Calibration / Reserved": __ok_fault(self.status & 0x0040),
            "Backup Calibration / Reserved": __ok_fault(self.status & 0x0080),
            "Event Trap": __ok_fault(self.status & 0x0100),
            # 0x0200 is reserved
            "Reserved / DCP RS-422 Chip": __ok_fault(self.status & 0x0400),
            # 0x0800 is reserved
            "No Application": __ok_fault(self.status & 0x1000),
            "Application error": __ok_fault(self.status & 0x2000),
            # 0x4000 is reserved
            "Bootloader Active": "Bootloader" if self.status & 0x8000 else "Application",
        }
