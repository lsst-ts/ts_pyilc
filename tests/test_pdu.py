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
    ForceActuatorSetBoosterValveDCAGainRequest,
    ForceActuatorSetBoosterValveDCAGainResponse,
    HardpointForceAndStatusRequest,
    HardpointForceAndStatusResponse,
    HardpointStepMotorMoveRequest,
    HardpointStepMotorMoveResponse,
    ILCMode,
    ServerIDRequest,
    ServerIDResponse,
    ServerStatusRequest,
    ServerStatusResponse,
    SetILCTemporaryAddress,
)
from lsst.ts.pyilc.pdu.utils import ILCFunction

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
            0x11,
            b"\x11\x2b\x00\x00\x17\x85\x53\x34\x02\x02\x02\x02\x09\x00\x50\x6e\x65\x75\x6d\x61\x74\x69\x63\x20\x49\x4c\x43\x20\x28\x63\x29\x32\x30\x31\x37\x20\x41\x55\x52\x41\x2d\x4c\x53\x53\x54",
        ),
        (
            0x12,
            b"\x12\x01\x02\x03\x04\x05",
        ),
        (
            0x41,
            b"\x41\x00\x01",
        ),
        (
            0x42,
            b"\x42\xff\xff\xff\xf8B)\xae\x14",
        ),
        (
            0x43,
            b"\x43\x02\x00\x00\x00\x2a\xc2-\xae\x14",
        ),
        (
            0x48,
            b"\x48\x17",
        ),
        (
            0x49,
            b"\x49",
        ),
    ]

    @parameterized.expand(responses)
    def test_client_decode(self, code: int, frame: bytes) -> None:
        """Tests PDUs decode and encode methods."""
        server.add_pdu(ServerIDRequest, ServerIDResponse)
        server.add_pdu(ServerStatusRequest, ServerStatusResponse)
        server.add_pdu(ILCMode, ILCMode)
        server.add_pdu(HardpointStepMotorMoveRequest, HardpointStepMotorMoveResponse)
        server.add_pdu(HardpointForceAndStatusRequest, HardpointForceAndStatusResponse)
        server.add_pdu(SetILCTemporaryAddress, SetILCTemporaryAddress)
        server.add_pdu(
            ForceActuatorSetBoosterValveDCAGainRequest, ForceActuatorSetBoosterValveDCAGainResponse
        )

        pdu = self.server.decode(frame)

        assert pdu.encode() == frame[1:]

        if pdu.function_code == ILCFunction.REPORT_SERVER_ID:
            frame_size = pdu.calculateRtuFrameSize(b"\x01" + frame)
            if frame_size == 27:
                assert pdu.unique_id == 0x010203040506
                assert pdu.ilc_app_type == 0x07
                assert pdu.network_node_type == 0x08
                assert pdu.ilc_selected_options == 0x09
                assert pdu.network_node_options == 0x0A
                assert pdu.major_rev == 0x0B
                assert pdu.minor_rev == 0x0C
                assert pdu.firmware_name == "Test ILC !"
            elif frame_size == 48:
                assert pdu.unique_id == 0x000017855334
                assert pdu.ilc_app_type == 0x02
                assert pdu.network_node_type == 0x02
                assert pdu.ilc_selected_options == 0x02
                assert pdu.network_node_options == 0x02
                assert pdu.major_rev == 0x09
                assert pdu.minor_rev == 0x00
                assert pdu.firmware_name == "Pneumatic ILC (c)2017 AURA-LSST"
            else:
                self.fail(f"Unknow server_id 17 (0x11) frame size: {frame_size}.")

        elif pdu.function_code == ILCFunction.REPORT_SERVER_STATUS:
            assert pdu.mode == 0x01
            assert pdu.status == 0x0203
            assert pdu.faults == 0x0405
        elif pdu.function_code == ILCFunction.CHANGE_ILC_MODE:
            assert pdu.mode == 0x0001
        elif pdu.function_code == ILCFunction.HP_STEP_MOTOR_MOVE:
            assert pdu.ssi_encoder_position == -8
            self.assertAlmostEqual(pdu.load_cell_force, 42.42, places=4)
        elif pdu.function_code == ILCFunction.HP_FORCE_AND_STATUS:
            assert pdu.status == 2
            assert pdu.ssi_encoder_position == 42
            self.assertAlmostEqual(pdu.load_cell_force, -43.42, places=4)
        elif pdu.function_code == ILCFunction.SET_TEMP_ILC_ADDR:
            assert pdu.address == 0x17
        elif pdu.function_code == ILCFunction.FA_SET_BOOSTER_VALVE_DCA_GAINS:
            pass
        else:
            self.fail(
                f"Unhandled function code when checking decoding: {pdu.function_code} ({pdu.function_code:x})"
            )


if __name__ == "__main__":
    unittest.main()
