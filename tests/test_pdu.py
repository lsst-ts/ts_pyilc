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

import numpy as np
from parameterized import parameterized
from pymodbus.pdu import DecodePDU

from lsst.ts.pyilc.pdu import (
    ADCScanRate,
    ChangeILCMode,
    ForceActuatorForceAndStatusDAResponse,
    ForceActuatorForceAndStatusRequest,
    ForceActuatorForceDemandDARequest,
    ForceActuatorForceDemandDAResponse,
    ForceActuatorReadBoosterValveDCAGainsRequest,
    ForceActuatorReadBoosterValveDCAGainsResponse,
    ForceActuatorSetBoosterValveDCAGainsRequest,
    ForceActuatorSetBoosterValveDCAGainsResponse,
    HardpointForceAndStatusRequest,
    HardpointForceAndStatusResponse,
    HardpointStepMotorMoveRequest,
    HardpointStepMotorMoveResponse,
    ReadCalibrationDataRequest,
    ReadCalibrationDataResponse,
    ReadDACValuesRequest,
    ReadDACValuesResponse,
    ReadMezzanineIDRequest,
    ReadMezzanineIDResponse,
    ReadMezzanineLVDTRequest,
    ReadMezzanineLVDTResponse,
    ReadMezzaninePressureRequest,
    ReadMezzaninePressureResponse,
    ReadMezzanineStatusRequest,
    ReadMezzanineStatusResponse,
    ReadMonitorSensorsRequest,
    ReadMonitorTemperatureSensorsResponse,
    ReadReheaterGainsRequest,
    ReadReheaterGainsResponse,
    Reset,
    ServerIDRequest,
    ServerIDResponse,
    ServerStatusRequest,
    ServerStatusResponse,
    SetADCChannelOffsetAndSensitivityRequest,
    SetADCChannelOffsetAndSensitivityResponse,
    SetADCScanRate,
    SetILCTemporaryAddress,
    SetReheaterGainsRequest,
    SetReheaterGainsResponse,
    ThermalDemandRequest,
    ThermalDemandResponse,
    ThermalStatusRequest,
    ThermalStatusResponse,
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
        (0x12, b"\x12\x01\x02\x03\x04\x05"),
        (0x41, b"\x41\x00\x01"),
        (0x42, b"\x42\xff\xff\xff\xf8B)\xae\x14"),
        (0x43, b"\x43\x4d\x00\x00\x00\x2a\xc2-\xae\x14"),
        (0x48, b"\x48\x17"),
        (0x49, b"\x49"),
        (0x4A, b"\x4aB)\xae\x14\xc2)\xb8R"),
        (0x4B, b"\x4b\x43C\x0e$Z\xc3\x0e$Z"),
        (0x4C, b"\x4c\x43\xc3\x0e$ZC\x0e$Z"),
        (0x50, b"\x50\x02"),
        (0x51, b"\x51"),
        (0x52, b"\x52\x01\x02\x03\x04\x05\x06\xff\xfe"),
        (0x58, b"\x58\x4f\xc2)\xb8R\x42B)\xae\x14"),
        (0x58, b"\x59\x45B)\xae\x14\x45\xc2)\xb8R"),
        (0x5C, b"\x5c"),
        (0x5D, b"\x5d\xc2)\xb8RB)\xae\x14"),
        (0x6B, b"\x6b"),
        (
            0x6E,
            b"\x6eB(p\xa4B(\xd7\nB)=qB)\xa3\xd7B*\n=B*p\xa4B*\xd7\nB+=qB+\xa3\xd7B,\n=B,p\xa4B,\xd7\nB-=qB-\xa3\xd7B.\n=B.p\xa4B.\xd7\nB/=qB/\xa3\xd7B0\n=B0p\xa4B0\xd7\nB1=qB1\xa3\xd7",
        ),
        (0x77, b"\x77B(p\xa4B(\xd7\nB)=qB)\xa3\xd7"),
        (0x78, b"\x78\x01\x02\x03\x04\x05\x42\x35\x04\x02"),
        (0x79, b"\x79\x01\x02"),
        (0x7A, b"\x7aB(p\xa4B(\xd7\n"),
        (0x54, b"\x54B(p\xa4B(\xd7\nB)=qB)\xa3\xd7"),
    ]

    @parameterized.expand(responses)
    def test_client_decode(self, code: int, frame: bytes) -> None:
        """Tests PDUs decode and encode methods."""
        server.add_pdu(ServerIDRequest, ServerIDResponse)
        server.add_pdu(ServerStatusRequest, ServerStatusResponse)
        server.add_pdu(ChangeILCMode, ChangeILCMode)
        server.add_pdu(HardpointStepMotorMoveRequest, HardpointStepMotorMoveResponse)
        server.add_pdu(HardpointForceAndStatusRequest, HardpointForceAndStatusResponse)
        server.add_pdu(SetILCTemporaryAddress, SetILCTemporaryAddress)
        server.add_pdu(
            ForceActuatorSetBoosterValveDCAGainsRequest, ForceActuatorSetBoosterValveDCAGainsResponse
        )
        server.add_pdu(
            ForceActuatorReadBoosterValveDCAGainsRequest, ForceActuatorReadBoosterValveDCAGainsResponse
        )
        server.add_pdu(ForceActuatorForceDemandDARequest, ForceActuatorForceDemandDAResponse)
        server.add_pdu(ForceActuatorForceAndStatusRequest, ForceActuatorForceAndStatusDAResponse)
        server.add_pdu(SetADCScanRate, SetADCScanRate)
        server.add_pdu(SetADCChannelOffsetAndSensitivityRequest, SetADCChannelOffsetAndSensitivityResponse)
        server.add_pdu(ReadDACValuesRequest, ReadDACValuesResponse)
        server.add_pdu(ThermalDemandRequest, ThermalDemandResponse)
        server.add_pdu(ThermalStatusRequest, ThermalStatusResponse)
        server.add_pdu(SetReheaterGainsRequest, SetReheaterGainsResponse)
        server.add_pdu(ReadReheaterGainsRequest, ReadReheaterGainsResponse)
        server.add_pdu(Reset, Reset)
        server.add_pdu(ReadCalibrationDataRequest, ReadCalibrationDataResponse)
        server.add_pdu(ReadMezzaninePressureRequest, ReadMezzaninePressureResponse)
        server.add_pdu(ReadMezzanineIDRequest, ReadMezzanineIDResponse)
        server.add_pdu(ReadMezzanineStatusRequest, ReadMezzanineStatusResponse)
        server.add_pdu(ReadMezzanineLVDTRequest, ReadMezzanineLVDTResponse)

        server.add_pdu(ReadMonitorSensorsRequest, ReadMonitorTemperatureSensorsResponse)

        pdu = self.server.decode(frame)

        assert pdu.encode() == frame[1:]

        def __assert_array(actual: list[float], start: float) -> None:
            for a, b in zip(actual, np.arange(start, start + 0.1 * len(actual), 0.1)):
                self.assertAlmostEqual(a, b, places=4)

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
            assert pdu.ilc_fault
            assert pdu.limit_switch_cw
            assert pdu.limit_switch_ccw
            assert pdu.communication_counter == 4
            assert pdu.ssi_encoder_position == 42
            self.assertAlmostEqual(pdu.load_cell_force, -43.42, places=4)
        elif pdu.function_code == ILCFunction.SET_TEMP_ILC_ADDR:
            assert pdu.address == 0x17
        elif pdu.function_code == ILCFunction.FA_SET_BOOSTER_VALVE_DCA_GAINS:
            pass
        elif pdu.function_code == ILCFunction.FA_READ_BOOSTER_VALVE_DCA_GAINS:
            self.assertAlmostEqual(pdu.axial_gain, 42.42, places=4)
            self.assertAlmostEqual(pdu.lateral_gain, -42.43, places=4)
        elif pdu.function_code == ILCFunction.FA_FORCE_DEMAND:
            assert pdu.ilc_fault
            assert pdu.dca_fault
            assert pdu.communication_counter == 4
            self.assertAlmostEqual(pdu.axial_cell_force, 142.142, places=4)
            self.assertAlmostEqual(pdu.lateral_cell_force, -142.142, places=4)
        elif pdu.function_code == ILCFunction.FA_FORCE_AND_STATUS:
            assert pdu.ilc_fault
            assert pdu.dca_fault
            assert pdu.communication_counter == 4
            self.assertAlmostEqual(pdu.axial_cell_force, -142.142, places=4)
            self.assertAlmostEqual(pdu.lateral_cell_force, 142.142, places=4)
        elif pdu.function_code == ILCFunction.SET_ADC_SCANRATE:
            assert pdu.scan_rate == ADCScanRate.RATE_100
        elif pdu.function_code == ILCFunction.SET_ADC_CHANNEL_OFFSET:
            pass
        elif pdu.function_code == ILCFunction.READ_DAC_VALUES:
            assert pdu.dac1_axial_push == 0x0102
            assert pdu.dac2_axial_pull == 0x0304
            assert pdu.dac3_lateral_push == 0x0506
            assert pdu.dac4_lateral_pull == 0xFFFE
        elif pdu.function_code == ILCFunction.TS_DEMAND:
            assert pdu.ilc_fault
            assert pdu.heater_disabled
            assert pdu.breaker_1
            assert pdu.breaker_2
            assert pdu.communication_counter == 4
            self.assertAlmostEqual(pdu.differential_temperature, -42.43, places=4)
            assert pdu.fan_rpm == 0x42
            self.assertAlmostEqual(pdu.absolute_temperature, 42.42, places=4)
        elif pdu.function_code == ILCFunction.TS_STATUS:
            assert pdu.ilc_fault
            assert not pdu.heater_disabled
            assert pdu.breaker_1
            assert not pdu.breaker_2
            assert pdu.communication_counter == 4
            self.assertAlmostEqual(pdu.differential_temperature, 42.42, places=4)
            assert pdu.fan_rpm == 69
            self.assertAlmostEqual(pdu.absolute_temperature, -42.43, places=4)
        elif pdu.function_code == ILCFunction.SET_REHEATER_GAINS:
            pass
        elif pdu.function_code == ILCFunction.READ_REHEATER_GAINS:
            self.assertAlmostEqual(pdu.p, -42.43, places=4)
            self.assertAlmostEqual(pdu.i, 42.42, places=4)
        elif pdu.function_code == ILCFunction.RESET_SERVER:
            pass
        elif pdu.function_code == ILCFunction.READ_CALIBRATION_DATA:
            __assert_array(pdu.main_adc_calibration, 42.11)
            __assert_array(pdu.main_sensor_offset, 42.51)
            __assert_array(pdu.main_sensor_sensitivity, 42.91)

            __assert_array(pdu.backup_adc_calibration, 43.31)
            __assert_array(pdu.backup_sensor_offset, 43.71)
            __assert_array(pdu.backup_sensor_sensitivity, 44.11)
        elif pdu.function_code == ILCFunction.READ_MEZZANINE_PRESSURE:
            self.assertAlmostEqual(pdu.axial_push, 42.11, places=4)
            self.assertAlmostEqual(pdu.axial_pull, 42.21, places=4)
            self.assertAlmostEqual(pdu.lateral_pull, 42.31, places=4)
            self.assertAlmostEqual(pdu.lateral_push, 42.41, places=4)
        elif pdu.function_code == ILCFunction.READ_MEZZANINE_ID:
            assert pdu.unique_id == 0x010203040542
            assert pdu.firmware_type_code == 53
            assert pdu.firmware_major_version == 4
            assert pdu.firmware_minor_version == 2
        elif pdu.function_code == ILCFunction.READ_MEZZANINE_STATUS:
            assert pdu.status == 0x0102
        elif pdu.function_code == ILCFunction.HM_READ_MEZZANINE_LVDT:
            self.assertAlmostEqual(pdu.lvdt_1, 42.11, places=4)
            self.assertAlmostEqual(pdu.lvdt_2, 42.21, places=4)

        elif pdu.function_code == ILCFunction.READ_MONITOR_SENSORS:
            __assert_array(pdu.temperature, 42.11)
        else:
            self.fail(
                f"Unhandled function code when checking decoding: {pdu.function_code} ({pdu.function_code:x})"
            )


if __name__ == "__main__":
    unittest.main()
