.. py:currentmodule:: lsst.ts.pyilc

.. _lsst.ts.pyilc:

#######################
lsst.ts.pyilc
#######################

This module allow communication with the Inner Loop Controllers (ILC)
electronics from Python. It provides custom ModbusPDU for request and responses
implemented as extensions of the Modbus protocol.

See LTS-346 and LTS-646 for protocol description.

Using lsst.ts.pyilc
===================

See cli.py, which provides convenient text-based interface for communication
with the ILC.


Contributing
============

``lsst.ts.pyilc`` is developed at https://github.com/lsst-ts/ts_pyilc.
You can find Jira issues for this module under the `ts_pyilc <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20component%20%3D%20ts_pyilc>`_ component.

Script reference
================

ilccli
------

Command line client for ILCs. The basic command line session might look as follow:

.. code-block::

	user:~$ ilccli
	> tcp localhost 5020
	Connected to localhost:5020. Type 'help' for commands, 'exit' or 'quit' to exit.

	AsyncModbusTcpClient localhost:5020> help
	Usage:  [OPTIONS] COMMAND [ARGS]...

	Options:
	  --help  Show this message and exit.

	Commands:
	  address                         Change default address.
	  change-ilc-mode                 Command ILC to change its mode.
	  debug                           Log every command.
	  force-actuator-set-booster-valve-dca-gain
					  Set booster valves DCA gains.
	  hardpoint-force-and-status      Command ILC to move...
	  hardpoint-step-motor-move       Command ILC to move...
	  report-server-id                Read coils or registers from...
	  report-server-status            Report ILC status - mode,...
	  serial                          Open connection to serial port.
	  set-ilc-temporary-address       Set ILC temporary address.
	  tcp                             Connect to TCP/IP bridge.
	AsyncModbusTcpClient localhost:5020> report-server-id
	Unique ID: 2211975595527 (0x020304050607)
	ILC Application Type: 250
	Network Node Type: 0xFF
	ILC Selected Options: 0xFD
	Network Node Options: FC
	Firmware Version: 245.255
	Firmware Name: Simulated ILC!
	AsyncModbusTcpClient localhost:5020>:

run_ilcsimulator
----------------

ILC simulator. Provides TCP/IP connection to simulate ILC traffic.


Python API reference
====================

.. automodapi:: lsst.ts.pyilc
   :no-main-docstr:
   :no-inheritance-diagram:

Version History
===============

The version history of the pyilc CSC is in the following link.

.. toctree::
    version-history
    :maxdepth: 1
