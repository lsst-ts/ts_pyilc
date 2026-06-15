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

from lsst.ts.pyilc.pdu.firmware import (
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


class PduTestCase(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
