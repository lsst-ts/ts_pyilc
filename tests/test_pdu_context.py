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

import os
import unittest

from intelhex import IntelHex
from pymodbus.pdu import DecodePDU, ModbusPDU
from pymodbus.utilities import hexlify_packets

from lsst.ts.pyilc.pdu import ChangeILCMode, Context, ILCMode
from lsst.ts.pyilc.pdu.firmware import (
    EraseApplication,
    WriteApplicationPageResponse,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationResponse,
)
from lsst.ts.pyilc.pdu.utils import ILCFunction

server = DecodePDU(False)

ilc_mode = int(ILCMode.STANDBY)


class MockClient:
    def __init__(self, output: str):
        self.output_file = open(output)

    async def connect(self) -> None:
        pass

    def register(self, pdu: ModbusPDU) -> None:
        pass

    async def execute(self, no_return: bool, request: ModbusPDU) -> ModbusPDU:
        req = request.x_encode()
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


class PduContextTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_flashing(self) -> None:
        def data_file(filename: str) -> str:
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", filename)

        hex_file = IntelHex(data_file("ILC-3.hex"))
        test_client = MockClient(data_file("ILC-3.out"))

        context = Context()
        await context.connect(test_client)

        end_status = await context.flash(0x11, hex_file)

        assert end_status == 0


if __name__ == "__main__":
    unittest.main()
