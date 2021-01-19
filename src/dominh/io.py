
# Copyright (c) 2021, G.A. vd. Hoorn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# author: G.A. vd. Hoorn


import re

from . constants import HLPR_SCALAR_VAR
from . constants import IO_OFF
from . constants import IO_ON
from . exceptions import DominhException
from . helpers import exec_kcl
from . helpers import read_helper


def io_write(conx, port_type, idx, val, check=False):
    """Set port 'idx' of type 'port_type' to value 'val'.

    Valid values for 'port_type':

        BOOLEAN:
        - DIN
        - DOUT
        - RDO
        - OPOUT
        - TPOUT
        - WDI
        - WDO
        INTEGER:
        - AIN
        - AOUT
        - GIN
        - GOUT

    TODO: use an enum to limit port types
    TODO: add proper support for Group IO and Analog

    :param port_type: Type of port to write to (see docstring for accepted
    values)
    :type port_type: str
    :param idx: Index of the port to write to
    :type idx: int
    :param val: Value to write to the port
    :type val: int
    :param check: Whether to check the result of the write
    :type check: bool
    :returns: Nothing if check==False. Otherwise success of the write
    operation in the form of a bool
    :rtype: None or bool (see above)
    """
    ret = exec_kcl(
        conx, cmd=f'set port {port_type}[{idx}]={val}',
        wait_for_response=check)
    if not check:
        return

    # get some simple errors out of the way
    ret = ret.strip()
    if 'Port name expected' in ret:
        raise DominhException(
            f"Illegal port type identifier: '{port_type}'")
    if 'No ports of this type' in ret:
        raise DominhException(
            f"Controller does not have ports of this type: '{port_type}'")
    if 'Illegal port number' in ret:
        raise DominhException(
            f"Illegal port number for port {port_type}: {idx}")
    if 'Value out of range' in ret:
        raise DominhException(
            f"Value out of range for port type {port_type}: {val}")
    if 'ERROR' in ret:
        raise DominhException(
            "Unrecognised error trying to set port:\n"
            f"\n________________\n\n{ret}\n________________")

    # check for successful write
    is_ok = re.match(r'Value was: (0|1).*Value is:  (0|1)', ret, re.DOTALL)
    return is_ok and is_ok.group(2) == str(val)


def io_write_dout(conx, idx, val):
    """Write 'val' to 'DOUT[idx]'.

    :param idx: Index to write to
    :type idx: int
    :param val: Value to write
    :type val: int
    """
    io_write(conx, 'DOUT', idx, val)


def io_write_rout(conx, idx, val):
    """Write 'val' to 'ROUT[idx]'.

    :param idx: Index to write to
    :type idx: int
    :param val: Value to write
    :type val: int
    """
    io_write(conx, 'ROUT', idx, val)


def io_read(conx, port_type, idx):
    """Read port 'idx' of type 'port_type'.

    Valid values for 'port_type':

        BOOLEAN:
        - BRAKE
        - DIN
        - DOUT
        - ESTOP
        - LDIN
        - LDOUT
        - PLCIN
        - PLCOUT
        - RDI
        - RDO
        - SOPIN
        - SOPOUT
        - TOOL
        - TPIN
        - TPOUT
        - UOPIN
        - UOPOUT
        - WDI
        - WDO
        - WSIN
        - WSOUT
        INTEGER:
        - ANIN
        - ANOUT
        - GPIN
        - GPOUT
        - LANIN
        - LANOUT

    From: R-J3iC Controller Internet Options Setup and Operations Manual
    (MAROCINOP08051E REV B).

    TODO: use an enum to limit port types
    TODO: add proper support for Group IO and Analog

    :param port_type: Type of port to read from (see docstring for accepted
    values)
    :type port_type: str
    :param idx: Index of the port to read from
    :type idx: int
    :returns: Value of the port at 'port_type[idx]', encoded as 'ON', 'OFF'
    or a numerical value (depending on how the controller's web server
    represents values for the port type)
    :rtype: str
    """
    port_type = port_type.upper()
    port_id = f'{port_type}[{idx}]'
    ret = read_helper(
        conx, helper=HLPR_SCALAR_VAR, params={'_reqvar': port_id})

    # check for some common problems
    if 'unknown port type name' in ret[port_id].lower():
        raise DominhException(
            f"Illegal port type identifier: '{port_type}'")
    if 'no ports of this type' in ret[port_id].lower():
        raise DominhException(
            f"Controller does not have ports of this type: '{port_type}'")
    if 'illegal port number' in ret[port_id].lower():
        raise DominhException(
            f"Illegal port number for port {port_type}: {idx}")

    return ret[port_id]


def io_read_sopout(conx, idx):
    """Read from 'SOPOUT[idx]'.

    :param idx: Index to read from
    :type idx: int
    :returns: Current state of 'SOPOUT[idx]'
    :rtype: int
    """
    if io_read(conx, 'SOPOUT', idx) == 'ON':
        return IO_ON
    return IO_OFF


def io_read_sopin(conx, idx):
    """Read from 'SOPIN[idx]'.

    :param idx: Index to read from
    :type idx: int
    :returns: Current state of 'SOPIN[idx]'
    :rtype: int
    """
    if io_read(conx, 'SOPIN', idx) == 'ON':
        return IO_ON
    return IO_OFF


def io_read_uopout(conx, idx):
    """Read from 'UOPOUT[idx]'.

    :param idx: Index to read from
    :type idx: int
    :returns: Current state of 'UOPOUT[idx]'
    :rtype: int
    """
    if io_read(conx, 'UOPOUT', idx) == 'ON':
        return IO_ON
    return IO_OFF


def io_read_rout(conx, idx):
    """Read from 'RDO[idx]'.

    :param idx: Index to write to
    :type idx: int
    :returns: Current state of 'RDO[idx]'
    :rtype: int
    """
    if io_read(conx, 'RDO', idx) == 'ON':
        return IO_ON
    return IO_OFF
