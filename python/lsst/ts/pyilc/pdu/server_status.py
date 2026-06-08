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

from .utils import ILCFunction, ILCRequest

__all__ = ["ServerStatusRequest", "ServerStatusResponse"]

import struct

from pymodbus.pdu import ModbusPDU


class ServerStatusRequest(ILCRequest):
    """Request server status."""

    function_code = ILCFunction.REPORT_SERVER_STATUS


class ServerStatusResponse(ModbusPDU):
    """Report server status response."""

    function_code = ILCFunction.REPORT_SERVER_STATUS
    rtu_frame_size = 5

    def __init__(self, dev_id: int = 255):
        super().__init__(dev_id=dev_id)
        self.mode: int = 0
        self.status: int = 0
        self.faults: int = 0

    def encode(self) -> bytes:
        return struct.pack(">BHH", self.mode, self.status, self.faults)

    def decode(self, data: bytes) -> None:
        (self.mode, self.status, self.faults) = struct.unpack(">BHH", data)
