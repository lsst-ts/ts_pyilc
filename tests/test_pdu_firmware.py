# This file is part of ts_pyilc.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import unittest

from parameterized import parameterized
from pymodbus.pdu import DecodePDU

from lsst.ts.pyilc.pdu.firmware import (
    CRC,
    EraseApplication,
    WriteApplicationPageRequest,
    WriteApplicationPageResponse,
    WriteApplicationStatesRequest,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationRequest,
    WriteVerifyApplicationResponse,
)
from lsst.ts.pyilc.pdu.utils import ILCFunction

server = DecodePDU(False)
client = DecodePDU(False)


class PduTestCase(unittest.TestCase):
    requests = [
        b"\x64\xed\x6e\x2c\x00\x70\x38\x43\x80",
        b"\x65",
        b"\x66\x8d\x00\x00\xc0\x00\x80\xeb\x10\x07\x98\x6e\xff\x07\x00\x00\xe0\x20\x00\x3a\x30\xc3\xb3\x8b\xff\x07\x00\x40\xeb\x00\x4f\x78\x06\x00\x37\x1e\x84\xfb\xa9\xff\x07\x61\xbf\x20\x81\x00\x44\x80\x48\x78\x1e\x4f\xe8\x1e\x40\x78\xe7\x4f\x50\xf7\xff\x36\xd9\xff\x07\x00\x00\xe0\x03\x00\x3a\x00\x00\xeb\x10\x07\x98\x0c\x00\x37\x00\x40\xeb\x00\x4f\x78\x06\x00\x37\x9e\x80\xfb\x60\xbf\x20\x00\x80\x40\xf1\xc3\xb3\x01\x48\x78\x1e\x4f\xe8\x1e\x40\x78\xe7\x4f\x50\xf7\xff\x36\x1e\x00\x90\x4f\x04\x78\x00\x80\xfa\x00\x00\x06\x08\x00\xfa\x10\x07\x98\x21\x07\x98\x32\x07\x98\x1e\x01\x90\xae\x01\x90\x44\x18\xdd\xcc\x10\xde\x81\x00\x70\x44\x10\xdd\x00\x01\xbe\x00\x00\x20\x11\x0e\x20\x80\xea\x07\x00\x00\x78\x00\x0f\xe9\x9e\x00\x78\xc1\x11\x88\xbe\x00\x90\x00\x80\x28\x01\x00\x70\x80\x11\x88\x00\x40\x22",
        b"\x67",
    ]

    responses = [
        b"\x64",
        b"\x65",
        b"\x66",
        b"\x67\x42\x43",
    ]

    def setUp(self) -> None:
        print("setUp")

    @parameterized.expand(requests)
    def test_server_decode(self, frame: bytes) -> None:
        """Tests PDUs decode and encode methods on server side."""
        server.add_pdu(WriteApplicationStatesResponse, WriteApplicationStatesRequest)
        server.add_pdu(EraseApplication, EraseApplication)
        server.add_pdu(WriteApplicationPageResponse, WriteApplicationPageRequest)
        server.add_pdu(WriteVerifyApplicationResponse, WriteVerifyApplicationRequest)

        pdu = server.decode(frame)

        assert pdu.x_encode() == frame[1:]

        if pdu.function_code == ILCFunction.WRITE_APPLICATION_STATES:
            pass
        elif pdu.function_code == ILCFunction.ERASE_APPLICATION:
            pass
        elif pdu.function_code == ILCFunction.WRITE_APPLICATION_PAGE:
            assert pdu.start_address == 0x8D00
            assert pdu.length == 0xC0
            assert pdu.data == frame[5:]

    @parameterized.expand(responses)
    def test_client_decode(self, frame: bytes) -> None:
        """Tests PDUs decode and encode methods on client side."""
        client.add_pdu(WriteApplicationStatesRequest, WriteApplicationStatesResponse)
        client.add_pdu(EraseApplication, EraseApplication)
        client.add_pdu(WriteApplicationPageRequest, WriteApplicationPageResponse)
        client.add_pdu(WriteVerifyApplicationRequest, WriteVerifyApplicationResponse)

        pdu = client.decode(frame)

        assert pdu.x_encode() == frame[1:]

        if pdu.function_code == ILCFunction.WRITE_APPLICATION_STATES:
            pass
        elif pdu.function_code == ILCFunction.ERASE_APPLICATION:
            pass
        elif pdu.function_code == ILCFunction.WRITE_APPLICATION_PAGE:
            pass
        elif pdu.function_code == ILCFunction.WRITE_VERIFY_APPLICATION:
            assert pdu.status == 0x4243
        else:
            self.fail(
                f"Unhandled function code when checking decoding: {pdu.function_code} ({pdu.function_code:x})"
            )

    def test_crc(self) -> None:
        crc = CRC()

        crc.append(b"\x12\x12")

        assert crc.crc == 0x1D8D

        crc = CRC()

        crc.append(b"\x12\x66\x34\x00\x00\xc0\x00\x00\x00\x32\x00\xf9\x00\x00\x06\x32\x00\xf8\x00\x05\x24")
        crc.append(b"\x00\x3b\x88\xf2\xff\x37\x32\x00\xf8\x91\x01\x88\x41\x00\x24\x01\x3b\x88\x02\x08\xbb")
        crc.append(b"\xec\xff\x37\x03\xf0\xa2\x88\x9f\xbe\x8a\x9f\xbe\x8c\x1f\x78\xfa\x00\x07\x01\x01\x33")
        crc.append(b"\x64\x50\xe1\x4f\x00\x32\x64\x20\xe1\x52\x00\x32\x03\x82\x6c\x07\x00\x3b\x09\x05\xd0")
        crc.append(b"\x03\x06\xd0\x82\x0f\x54\x0c\x06\x5d\x02\x00\x39\x02\x00\x32\x89\x01\x78\x03\x06")
        crc.append(b"\x78\x85\x82\x55\x04\x00\x3d\x00\x03\xfd\x81\x03\xfd\x85\x02\xea\x8b\x85\x42\x84")
        crc.append(b"\x0f\x72\x02\x00\x3b\x60\x00\x10\xe0\x80\x18\x60\x11\xb8\x00\x05\xeb\x7a\x28\xe1\x0a")
        crc.append(b"\x00\x39\x06\x00\x78\xc7\x5d\xdd\xf7\x07\xb2\x87\x80\x75\x2d\x00\x37\x82\x81\x71")
        crc.append(b"\x0a\x01\x78\x61\x05\x60\x81\x80\xd1\x00\x80\xd3\x85\x02\xe9\xf9\xff\x3b")
        crc.append(b"\x06\x04\x40\x87\x84\x48\x02\x00\x3b\x60\x04\x14\xe0\x84\x1c")

        assert crc.crc == 0x371A


if __name__ == "__main__":
    unittest.main()
