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


import datetime
import re
import typing as t

from . import kliosop
from . import kliouop

from .constants import IO_OFF
from .constants import IO_ON
from .constants import JSON_REASON
from .constants import JSON_SUCCESS
from .exceptions import DominhException
from .ftp import FtpClient
from .helpers import exec_karel_prg
from .helpers import exec_kcl
from .io import io_read_sopin
from .io import io_read_sopout
from .io import io_read_uopout
from .variables import get_scalar_var
from .variables import set_scalar_var
from .web_server import disable_web_server_headers
from .web_server import enable_web_server_headers


def reset(conx) -> None:
    """Attempt to RESET the controller."""
    exec_kcl(conx, cmd='reset')


def select_tpe(conx, program: str) -> None:
    """Attempt to make 'program' the SELECTed program on the TP.

    Wraps the Karel SELECT_TPE(..) routine.

    NOTE: this method currently doesn't work reliably.

    Alternative approach: put controller in REMOTE mode and write to
    '$shell_wrk.$cust_start'.

    :param program: Name of the program to select.
    :type program: str
    """
    raise DominhException('Not implemented')
    ret = exec_karel_prg(conx, prg_name='dmh_selprg', params={'prog_name': program})
    if not ret[JSON_SUCCESS]:
        raise DominhException("Select_TPE error: " + ret[JSON_REASON])


def get_general_override(conx) -> int:
    """Retrieve the currently configured General Override.

    :returns: Value of $MCR.$GENOVERRIDE
    :rtype: int
    """
    return int(get_scalar_var(conx, name='$MCR.$GENOVERRIDE'))


def set_general_override(conx, val: int) -> None:
    """Set the General Override to 'val'.

    :param val: New value for $MCR.$GENOVERRIDE
    :type val: int
    """
    set_scalar_var(conx, name='$MCR.$GENOVERRIDE', val=val)


def list_programs(conx, types: t.List[str] = []) -> t.List[t.Tuple[str, str]]:
    """Retrieve the list of all programs stored on the controller.

    NOTE: this is a rather naive implementation which should not be used in
    tight loops or when high performance is required.

    NOTE: this method is expensive and slow, as it parses a web page.

    :param types: A list of program types to include in the returned
    result.
    Legal values are those used by the controller when displaying lists of
    programs in the pages served by the Fanuc web server (fi: PC, MACRO,
    TP, VR, etc)
    :type types: list[str]
    :returns: List of tuples containing names and type of programs on the
    controller in the order they are returned
    :rtype: list[tuple(str, str)]
    """
    # TODO: check whether headers are currently enabled and restore state
    # after having used 'show progs'
    disable_web_server_headers(conx)
    # TODO: see whether FTP-ing 'prgstate.dg' would be faster
    ret = exec_kcl(conx, cmd='show progs', wait_for_response=True)
    enable_web_server_headers(conx)

    # parse returned list
    # TODO: we only return '(name, type)' tuples for now
    matches = re.findall(r'(\S+)\s+(\S+)\s+Task', ret.strip(), re.DOTALL)

    types = [t.lower() for t in types]
    return [m for m in matches if (types and m[1].lower() in types) or not types]


def get_controller_series(conx) -> str:
    """Returns the controller series identifier (ie: R-30iA, 30iB, etc).

    Note: this method maps known major versions to controller series. It
    does not use any value retrieved from the controller directly.

    :returns: The series identifier of the controller
    :rtype: str
    """
    software_version = get_system_software_version(conx)
    major = int(re.match(r'V(\d)\.', software_version).group(1))
    return {
        7: 'R-30iA',
        8: 'R-30iB',
        9: 'R-30iB+',
    }.get(major, f'Unknown ("{software_version}")')


def get_application(conx) -> str:
    """Returns the application identifier installed on the controller.

    The application is the '*Tool', such as HandlingTool, SpotTool, etc.

    :returns: The application installed on the controller.
    :rtype: str
    """
    APPL_ID_IDX = 1
    return get_scalar_var(conx, name=f'$application[{APPL_ID_IDX}]')


def get_system_software_version(conx) -> str:
    """Returns the version (major.minor and patch) of the system software.

    :returns: The version of the system software on the controller
    :rtype: str
    """
    APPL_VER_IDX = 2
    return get_scalar_var(conx, name=f'$application[{APPL_VER_IDX}]')


def in_auto_mode(conx) -> bool:
    """Determine whether the controller is in AUTO or one of the MANUAL
    modes.

    Wraps the Karel IN_AUTO_MODE routine.

    NOTE: this method is moderately expensive, as it executes a Karel
    program on the controller.

    :returns: True if the controller is in AUTO mode
    :rtype: bool
    """
    ret = exec_karel_prg(conx, prg_name='dmh_autom')
    if not ret[JSON_SUCCESS]:
        raise DominhException("Select_TPE error: " + ret[JSON_REASON])
    return ret['in_auto_mode']


def tp_enabled(conx) -> bool:
    """Determine whether the Teach Pendant is currently enabled.

    Checks SOP output index 7 (from kliosop.kl).

    :returns: True if the TP is 'ON'
    :rtype: bool
    """
    return io_read_sopout(conx, idx=kliosop.SOPO_TPENBL) == IO_ON


def is_faulted(conx) -> bool:
    """Determine whether the controller is currently faulted.

    Checks SOP output index 3 (from kliosop.kl).

    :returns: True if there is an active fault on the controller
    :rtype: bool
    """
    return io_read_sopout(conx, idx=kliosop.SOPO_FAULT) == IO_ON


def is_e_stopped(conx) -> bool:
    """Determine whether the controller is currently e-stopped.

    Checks SOP input index 0 (from kliosop.kl).

    :returns: True if the e-stop is active
    :rtype: bool
    """
    # active low input
    return io_read_sopin(conx, idx=kliosop.SOPI_ESTOP) == IO_OFF


def in_remote_mode(conx) -> bool:
    """Determine whether the controller is in remote mode.

    Checks SOP output index 0 (from kliosop.kl).

    :returns: True if a program is running.
    :rtype: bool
    """
    return io_read_sopout(conx, idx=kliosop.SOPO_REMOTE) == IO_ON


def is_program_running(conx) -> bool:
    """Determine whether the controller is executing a program.

    NOTE: this does not check for any specific program, but will return
    True whenever the currently selected program (or any of its children)
    are not PAUSED or ABORTED.

    Checks UOP output index 3 (from kliouop.kl).

    :returns: True if a program is running.
    :rtype: bool
    """
    return io_read_uopout(conx, idx=kliouop.UOPO_PROGRUN) == IO_ON


def is_program_paused(conx) -> bool:
    """Determine whether there is a paused program on the controller.

    NOTE: this does not check for any specific program, but will return
    True whenever the currently selected program is PAUSED.

    Checks UOP output index 4 (from kliouop.kl).

    :returns: True if a program is paused.
    :rtype: bool
    """
    return io_read_uopout(conx, idx=kliouop.UOPO_PAUSED) == IO_ON


def list_errors(conx) -> t.List[t.Tuple[int, str, str, str, str, str]]:
    """Return list of all errors.

    The list returned contains each error as an element in the list. Each
    element is a tuple with the following layout:

        (seq nr, date, err msg, err detail, level, state mask)

    The 'err detail' and 'level' elements are not always present and thus
    may be empty.

    NOTE: this method is expensive and slow, as it retrieves a file from
    the controller over FTP and parses it.

    :returns: A list of all errors and their details
    :rtype: list(tuple(int, str, str, str, str, str))
    """
    ftpc = FtpClient(conx.host, timeout=conx.request_timeout)
    # log in using username and pw, if provided by user
    if conx.ftp_auth:
        user, pw = conx.ftp_auth
        ftpc.connect(user=user, pw=pw)
    else:
        ftpc.connect()
    errs = ftpc.get_file_as_str('/md:/errall.ls')

    res = []
    for line in errs.decode('ascii').splitlines():
        if ('Robot Name' in line) or (line == ''):
            continue
        fields = list(map(str.strip, line.split('"')))
        level_state = fields[4].split()
        if len(level_state) > 1:
            (
                err_level,
                err_state,
            ) = level_state
        else:
            err_level, err_state, = (
                '',
                level_state[0],
            )
        res.append(
            (int(fields[0]), fields[1], fields[2], fields[3], err_level, err_state)
        )
    return res


def get_active_prog(conx) -> str:
    ret = get_scalar_var(conx, name='$SHELL_WRK.$ACTIVEPROG')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_curr_routine(conx) -> str:
    ret = get_scalar_var(conx, name='$SHELL_WRK.$ROUT_NAME')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_curr_line(conx) -> int:
    ret = get_scalar_var(conx, name='$SHELL_WRK.$CURR_LINE')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return int(ret)


def get_num_groups(conx) -> int:
    ret = get_scalar_var(conx, name='$SCR.$NUM_GROUP')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return int(ret)


def get_clock(conx) -> datetime.datetime:
    """Return the current date and time on the controller.

    NOTE: this method is rather slow, as it parses a web page.

    NOTE 2: the controller reports time with a resolution of 1 minute.

    :returns: Controller date and time.
    :rtype: datetime.datetime
    """
    ret = exec_kcl(conx, cmd='show clock', wait_for_response=True)
    # date & time is on the second line of the output
    stamp = ret.strip().split('\n')[1]
    return datetime.datetime.strptime(stamp, '%d-%b-%y %H:%M')
