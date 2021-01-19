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

from .comset import comset
from .constants import HLPR_RAW_VAR
from .exceptions import DominhException
from .helpers import get_stm
from .types import Config_t
from .types import JointPos_t
from .types import Position_t
from .variables import get_scalar_var


def get_strreg(conx, idx):
    """Retrieve the value stored in the string register at 'idx'.

    :param idx: The index of the register to retrieve.
    :type idx: int
    :returns: The string stored at index 'idx' in the string registers on
    the controller
    :rtype: str
    """
    # TODO: rather nasty hard-coded variable name
    # TODO: check for errors (fi idx too high)
    return get_scalar_var(conx, name=f'[*STRREG*]$STRREG[{idx}]')


def get_num_strreg(conx):
    """Retrieve total number of string registers available on the
    controller.

    :returns: value of [*STRREG*]$MAXSREGNUM.
    :rtype: int
    """
    return int(get_scalar_var(conx, name='[*STRREG*]$MAXSREGNUM'))


def get_numreg(conx, idx):
    """Retrieve the value stored in the numerical register at 'idx'.

    :param idx: The index of the register to retrieve.
    :type idx: int
    :returns: Either the integer or the floating point number stored at
    index 'idx' in the numerical registers on the controller
    :rtype: int or float (see above)
    """
    ret = get_scalar_var(conx, name=f'$NUMREG[{idx}]')
    return float(ret) if '.' in ret else int(ret)


def set_numreg(conx, idx, val):
    """Update the value stored in 'R[idx]' to 'val'.

    Note: 'val' must be either int or float.

    :param idx: The index of the register to update
    :type idx: int
    :param val: The value to write to the register
    :type val: int or float
    """
    assert type(val) in [float, int]
    comset(conx, 'NUMREG', idx, val=val)


def get_posreg(conx, idx, group=1):
    """Return the position register at index 'idx' for group 'group'.

    NOTE: this method is expensive and slow, as it parses a web page.

    :param idx: Numeric ID of the position register.
    :type idx: int
    :param group: Numeric ID of the motion group the position register is
    associated with.
    :type group: int
    :returns: A tuple containing the pose and associated comment
    :rtype: tuple(Position_t, str) or tuple(JointPos_t, str)
    """
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    varname = f'$POSREG[{group},{idx}]'
    # use get_stm(..) directly here as what we get returned is not actually
    # json, and read_helper(..) will try to parse it as such and then fail
    ret = get_stm(conx, page=HLPR_RAW_VAR + '.stm', params={'_reqvar': varname})

    # use Jay's regex (thanks!)
    # TODO: merge with get_frame_var(..)
    match = re.findall(
        r"(?m)"
        r"\'([^']*)' "
        r"("
        r"Uninitialized"
        r"|"
        r"\r?\n"
        r"  Group: (\d)   Config: (F|N) (U|D) (T|B), (\d), (\d), (\d)\r?\n"
        r"  X:\s*(-?\d*.\d+|[*]+)   Y:\s+(-?\d*.\d+|[*]+)   Z:\s+(-?\d*.\d+|[*]+)\r?\n"  # noqa
        r"  W:\s*(-?\d*.\d+|[*]+)   P:\s*(-?\d*.\d+|[*]+)   R:\s*(-?\d*.\d+|[*]+)"  # noqa
        r"|"
        r"  Group: (\d)\r?\n"
        r"  (J1) =\s*(-?\d*.\d+|[*]+) deg   J2 =\s*(-?\d*.\d+|[*]+) deg   J3 =\s*(-?\d*.\d+|[*]+) deg \r?\n"  # noqa
        r"  J4 =\s*(-?\d*.\d+|[*]+) deg   J5 =\s*(-?\d*.\d+|[*]+) deg   J6 =\s*(-?\d*.\d+|[*]+) deg)",  # noqa
        ret.text,
    )

    if not match:
        raise DominhException(f"Could not match value returned for '{varname}'")

    posreg = match[0]
    if 'Uninitialized' in posreg:
        return (None, '')

    cmt = posreg[0]
    if posreg[16] == 'J1':
        # TODO: this doesn't work for non-6-axis systems
        jpos = list(map(float, posreg[17:24]))
        return (JointPos_t(*jpos), cmt)
    else:
        # some nasty fiddling
        # TODO: this won't work for non-6-axis systems
        f = posreg[3] == 'F'  # N
        u = posreg[4] == 'U'  # D
        t = posreg[5] == 'T'  # B
        turn_nos = list(map(int, posreg[6:9]))
        xyzwpr = list(map(float, posreg[9:15]))
        return (Position_t(Config_t(f, u, t, *turn_nos), *xyzwpr), cmt)
