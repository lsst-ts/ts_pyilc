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

__all__ = ["ReadMezzanineIDRequest", "ReadMezzanineIDResponse"]

import struct
from enum import IntEnum

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest


class ReadMezzanineIDRequest(ILCRequest):
    function_code = ILCFunction.READ_MEZZANINE_ID


class ReadMezzanineIDResponse(ModbusPDU):
    function_code = ILCFunction.READ_MEZZANINE_ID
    rtu_frame_size = 9

    class FirmwareTypeCode(IntEnum):
        UNKNOWN = 0
        DCA_BOOTLOADER = 51
        DCA_APPLICATION = 52
        DCP_BOOTLOADER = 51
        DCP_APPLICATION = 52

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id=dev_id)

        self.unique_id: int = 0
        self.firmware_type_code = self.FirmwareTypeCode.UNKNOWN
        self.firmware_major_version: int = 0
        self.firmware_minor_version: int = 0

    def encode(self) -> bytes:
        id_bytes = self.unique_id.to_bytes(6, byteorder="big", signed=False)
        return struct.pack(
            ">6s3B",
            id_bytes,
            self.firmware_type_code,
            self.firmware_major_version,
            self.firmware_minor_version,
        )

    def decode(self, data: bytes) -> None:
        (id_bytes, self.firmware_type_code, self.firmware_major_version, self.firmware_minor_version) = (
            struct.unpack(">6s3B", data)
        )
        self.unique_id = int.from_bytes(id_bytes, byteorder="big", signed=False)
