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
from enum import IntEnum

from pymodbus.datastore import ModbusDeviceContext
from pymodbus.pdu import ModbusPDU


class ILCFunction(IntEnum):
    """Modbus Function Codes for M1M3 ILCs based on LTS-646."""

    REPORT_SERVER_ID = 0x11  # 17
    REPORT_SERVER_STATUS = 0x12  # 18
    CHANGE_ILC_MODE = 0x41  # 65

    # Common commands
    FREEZE_SENSOR_VALUES = 0x44  # 68
    SET_TEMP_ILC_ADDR = 0x48  # 72
    SET_ADC_SCANRATE = 0x50  # 80
    SET_ADC_CHANNEL_OFFSET = 0x51  # 81
    RESET_SERVER = 0x6B  # 107
    READ_CALIBRATION = 0x6E  # 110

    READ_MEZZANINE_PRESSURE = 0x77  # 119
    READ_MEZZANINE_ID = 0x78  # 120
    READ_MEZZANINE_STATUS = 0x79  # 121

    # FA - Pneumatic ILC
    FA_SET_BOOSTER_VALVE_DCA_GAINS = 0x49  # 73
    FA_READ_BOOSTER_VALVE_DCA_GAINS = 0x4A  # 74
    FA_FORCE_DEMAND = 0x4B  # 75
    FA_FORCE_AND_STATUS = 0x4C  # 76

    # HP - Electromechanical (Hardpoint) and M2 ILC
    HP_STEP_MOTOR_MOVE = 0x42  # 66
    HP_FORCE_AND_STATUS = 0x43  # 67

    # HM - Harpoint Monitoring ILC
    HM_READ_MEZZANINE_LVDT = 0x7A  # 122

    # TS - Thermal ILC
    TS_DEMAND = 0x58  # 88
    TS_STATUS = 0x59  # 89

    # M2 - M2 Support System ILC
    READ_MONITOR_SENSORS = 0x54  # 84


class ServerIDRequest(ModbusPDU):
    """Request server ID data."""

    function_code = ILCFunction.REPORT_SERVER_ID

    def encode(self) -> bytes:
        return b""

    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        pdu = ServerIDResponse(dev_id=self.dev_id)

        pdu.unique_id = 0x020304
        pdu.firmware_name = "Simulated ILC!"

        return pdu


class ServerIDResponse(ModbusPDU):
    """
    FC 0x11 (17): Report Server ID
    Typically a simple request (just the FC) or a response containing ID data.
    """

    function_code = ILCFunction.REPORT_SERVER_ID
    rtu_byte_count_pos = 0

    def __init__(self, dev_id: int = 255):
        super().__init__(dev_id=dev_id)

        self.unique_id: int = 0
        self.ilc_app_type: int = 0
        self.network_node_type: int = 0
        self.ilc_selected_options: int = 0
        self.network_node_options: int = 0
        self.major_rev: int = 0
        self.minor_rev: int = 0
        self.firmware_name: str = ""

    def encode(self) -> bytes:
        id_bytes = self.unique_id.to_bytes(6, byteorder="big")
        fn_len = len(self.firmware_name)

        res = struct.pack(
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

        return res

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

        self.unique_id = int.from_bytes(id_bytes, byteorder="big")
        self.firmware_name = firmware_name.decode()


class ServerStatusRequest(ModbusPDU):
    function_code = ILCFunction.REPORT_SERVER_STATUS

    def encode(self) -> bytes:
        return b""


class ServerStatusResponse(ModbusPDU):
    function_code = ILCFunction.REPORT_SERVER_STATUS

    def __init__(self, dev_id: int = 255):
        super().__init__(dev_id=dev_id)
        self.mode: int = 0
        self.status: int = 0
        self.faults: int = 0

    def encode(self) -> bytes:
        return struct.pack(">BHH", self.mode, self.status, self.faults)

    def decode(self, data: bytes) -> None:
        (self.mode, self.status, self.faults) = struct.unpack(">BHH", data)


class ILCMode(ModbusPDU):
    function_code = ILCFunction.CHANGE_ILC_MODE

    def __init__(self, dev_id: int = 255, new_mode: int = 0xFFFF):
        super().__init__(dev_id=dev_id)
        self.mode = new_mode

    def encode(self) -> bytes:
        return struct.pack(">H", self.mode)

    def decode(self, data: bytes) -> None:
        self.mode = int.from_bytes(data, byteorder="big")
