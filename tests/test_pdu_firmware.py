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

import os
import unittest

from intelhex import IntelHex
from parameterized import parameterized
from pymodbus.pdu import DecodePDU, ModbusPDU
from pymodbus.utilities import hexlify_packets

from lsst.ts.pyilc.pdu import ChangeILCMode, ILCMode
from lsst.ts.pyilc.pdu.firmware import (
    CRC,
    EraseApplication,
    WriteApplicationPageRequest,
    WriteApplicationPageResponse,
    WriteApplicationStatesRequest,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationRequest,
    WriteVerifyApplicationResponse,
    flash,
)
from lsst.ts.pyilc.pdu.utils import ILCFunction

server = DecodePDU(False)

ilc_mode = int(ILCMode.STANDBY)


class MockClient:
    def __init__(self, output: str):
        self.output_file = open(output)

    async def execute(self, no_return: bool, request: ModbusPDU) -> ModbusPDU:
        req = request.encode()
        print("TestCase.execute:", str(request), request.function_code, hexlify_packets(req))
        expected_out = self.output_file.readline()

        if expected_out[:2] == "C>":
            outs = [int(h, 16) for h in expected_out[3:].split(" ")][2:-2]
            assert list(req) == outs

        if request.function_code == ILCFunction.CHANGE_ILC_MODE:
            global ilc_mode

            if request.mode != 0xFFFF:
                ilc_mode = request.mode

            return ChangeILCMode(dev_id=request.dev_id, new_mode=ilc_mode)
        elif request.function_code == ILCFunction.WRITE_APPLICATION_STATES:
            return WriteApplicationStatesResponse(dev_id=request.dev_id)
        elif request.function_code == ILCFunction.ERASE_APPLICATION:
            return EraseApplication(dev_id=request.dev_id)
        elif request.function_code == ILCFunction.WRITE_APPLICATION_PAGE:
            return WriteApplicationPageResponse(dev_id=request.dev_id)
        elif request.function_code == ILCFunction.WRITE_VERIFY_APPLICATION:
            return WriteVerifyApplicationResponse(dev_id=request.dev_id, status=0)

        raise RuntimeError(f"Cannot simulate request: {str(request)} {request.function_code}")


class PduTestCase(unittest.IsolatedAsyncioTestCase):
    server = DecodePDU(False)

    requests = [(0x64, b"\x64")]

    responses = [
        (
            0x64,
            b"\x64",
        ),
        (
            0x65,
            b"\x65",
        ),
        (
            0x66,
            b"\x66",
        ),
        (
            0x67,
            b"\x67\x42\x43",
        ),
    ]

    @parameterized.expand(responses)
    def test_client_decode(self, code: int, frame: bytes) -> None:
        """Tests PDUs decode and encode methods."""
        server.add_pdu(WriteApplicationStatesRequest, WriteApplicationStatesResponse)
        server.add_pdu(EraseApplication, EraseApplication)
        server.add_pdu(WriteApplicationPageRequest, WriteApplicationPageResponse)
        server.add_pdu(WriteVerifyApplicationRequest, WriteVerifyApplicationResponse)

        pdu = self.server.decode(frame)

        assert pdu.encode() == frame[1:]

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

    async def test_flashing(self) -> None:
        def data_file(filename: str) -> str:
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", filename)

        hex_file = IntelHex(data_file("ILC-3.hex"))
        test_client = MockClient(data_file("ILC-3.out"))

        end_status = await flash(test_client, 0x11, hex_file)

        assert end_status == 0


if __name__ == "__main__":
    unittest.main()
