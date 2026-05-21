# This file is part of ts_pyilc.
#
# Developed for the Rubin Observatory Telescope and Site System.
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

import unittest

from parameterized import parameterized
from pymodbus.pdu import DecodePDU

from lsst.ts.pyilc.pdu import (
    ILCFunction,
    ServerIDRequest,
    ServerIDResponse,
    ServerStatusRequest,
    ServerStatusResponse,
)

server = DecodePDU(False)


class PduTestCase(unittest.TestCase):
    server = DecodePDU(False)

    requests = [(0x11, b"\x11"), (0x12, b"\x12")]

    responses = [
        (
            0x11,
            b"\x11\x16\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x54\x65\x73\x74\x20\x49\x4c\x43\x20\x21",
        ),
        (
            0x12,
            b"\x12\x01\x02\x03\x04\x05",
        ),
    ]

    @parameterized.expand(responses)
    def test_client_decode(self, code: int, frame: bytes) -> None:
        server.add_pdu(ServerIDRequest, ServerIDResponse)
        server.add_pdu(ServerStatusRequest, ServerStatusResponse)

        pdu = self.server.decode(frame)

        if pdu.function_code == ILCFunction.REPORT_SERVER_ID:
            assert pdu.unique_id == 0x010203040506
            assert pdu.ilc_app_type == 0x07
            assert pdu.network_node_type == 0x08
            assert pdu.ilc_selected_options == 0x09
            assert pdu.network_node_options == 0x0A
            assert pdu.major_rev == 0x0B
            assert pdu.minor_rev == 0x0C
            assert pdu.firmware_name == "Test ILC !"
        elif pdu.function_code == ILCFunction.REPORT_SERVER_STATUS:
            assert pdu.mode == 0x01
            assert pdu.status == 0x0203
            assert pdu.faults == 0x0405


if __name__ == "__main__":
    unittest.main()
