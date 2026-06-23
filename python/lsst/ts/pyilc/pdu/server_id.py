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

__all__ = ["ServerIDRequest", "ServerIDResponse"]

import struct

from pymodbus.pdu import ModbusPDU

from .utils import ILCFunction, ILCRequest


class ServerIDRequest(ILCRequest):
    """Request ILC ID data."""

    function_code = ILCFunction.REPORT_SERVER_ID


class ServerIDResponse(ModbusPDU):
    """Report Server ID response."""

    function_code = ILCFunction.REPORT_SERVER_ID
    rtu_byte_count_pos = 2

    unique_id: int = 0
    ilc_app_type: int = 0
    network_node_type: int = 0
    ilc_selected_options: int = 0
    network_node_options: int = 0
    major_rev: int = 0
    minor_rev: int = 0
    firmware_name: str = ""

    def encode(self) -> bytes:
        id_bytes = self.unique_id.to_bytes(6, byteorder="big", signed=False)
        fn_len = len(self.firmware_name)

        return struct.pack(
            f">B6s6B{fn_len}s",
            fn_len + 12,
            id_bytes,
            self.ilc_app_type,
            self.network_node_type,
            self.ilc_selected_options,
            self.network_node_options,
            self.major_rev,
            self.minor_rev,
            self.firmware_name.encode(),
        )

    def decode(self, data: bytes) -> None:
        fn_len = data[0]

        if fn_len < 12:
            raise RuntimeError(
                f"Invalid lenght in Server ID packed - expected at least 12, received {fn_len}"
            )

        (
            id_bytes,
            self.ilc_app_type,
            self.network_node_type,
            self.ilc_selected_options,
            self.network_node_options,
            self.major_rev,
            self.minor_rev,
            firmware_name,
        ) = struct.unpack(f">6s6B{fn_len - 12}s", data[1:])

        self.unique_id = int.from_bytes(id_bytes, byteorder="big", signed=False)
        self.firmware_name = firmware_name.decode()
