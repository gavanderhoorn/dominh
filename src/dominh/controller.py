
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


def reset(self):
    """Attempt to RESET the controller."""
    self._exec_kcl(cmd='reset')


def select_tpe(self, program):
    """Attempt to make 'program' the SELECTed program on the TP.

    Wraps the Karel SELECT_TPE(..) routine.

    NOTE: this method currently doesn't work reliably.

    Alternative approach: put controller in REMOTE mode and write to
    '$shell_wrk.$cust_start'.

    :param program: Name of the program to select.
    :type program: str
    """
    raise DominhException('Not implemented')
    ret = self._exec_karel_prg(
        prg_name='dmh_selprg', params={'prog_name': program})
    if not ret[JSON_SUCCESS]:
        raise DominhException("Select_TPE error: " + ret[JSON_REASON])


def get_general_override(self):
    """Retrieve the currently configured General Override.

    :returns: Value of $MCR.$GENOVERRIDE
    :rtype: int
    """
    varname = '$MCR.$GENOVERRIDE'
    return int(self.get_scalar_var(varname))


def set_general_override(self, val):
    """Set the General Override to 'val'.

    :param val: New value for $MCR.$GENOVERRIDE
    :type val: int
    """
    varname = '$MCR.$GENOVERRIDE'
    self.set_scalar_var(varname, val)


def list_programs(self, types=[]):
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
    self._disable_web_server_headers()
    # TODO: see whether FTP-ing 'prgstate.dg' would be faster
    ret = self._exec_kcl(cmd='show progs', wait_for_response=True)
    self._enable_web_server_headers()

    # parse returned list
    # TODO: we only return '(name, type)' tuples for now
    matches = re.findall(r'(\S+)\s+(\S+)\s+Task', ret.strip(), re.DOTALL)

    types = [t.lower() for t in types]
    return [
        m for m in matches
        if (types and m[1].lower() in types) or not types
    ]


def get_controller_series(self):
    """Returns the controller series identifier (ie: R-30iA, 30iB, etc).

    Note: this method maps known major versions to controller series. It
    does not use any value retrieved from the controller directly.

    :returns: The series identifier of the controller
    :rtype: str
    """
    software_version = self.get_system_software_version()
    major = int(re.match(r'V(\d)\.', software_version).group(1))
    return {
        7: 'R-30iA',
        8: 'R-30iB',
        9: 'R-30iB+',
    }.get(major, f'Unknown ("{software_version}")')


def get_application(self):
    """Returns the application identifier installed on the controller.

    The application is the '*Tool', such as HandlingTool, SpotTool, etc.

    :returns: The application installed on the controller.
    :rtype: str
    """
    APPL_ID_IDX = 1
    return self.get_scalar_var(f'$application[{APPL_ID_IDX}]')


def get_system_software_version(self):
    """Returns the version (major.minor and patch) of the system software.

    :returns: The version of the system software on the controller
    :rtype: str
    """
    APPL_VER_IDX = 2
    return self.get_scalar_var(f'$application[{APPL_VER_IDX}]')


def in_auto_mode(self):
    """Determine whether the controller is in AUTO or one of the MANUAL
    modes.

    Wraps the Karel IN_AUTO_MODE routine.

    NOTE: this method is moderately expensive, as it executes a Karel
    program on the controller.

    :returns: True if the controller is in AUTO mode
    :rtype: bool
    """
    ret = self._exec_karel_prg(prg_name='dmh_autom')
    if not ret[JSON_SUCCESS]:
        raise DominhException("Select_TPE error: " + ret[JSON_REASON])
    return ret['in_auto_mode']


def tp_enabled(self):
    """Determine whether the Teach Pendant is currently enabled.

    Checks SOP output index 7 (from kliosop.kl).

    :returns: True if the TP is 'ON'
    :rtype: bool
    """
    state = self.io_read_sopout(idx=kliosop.SOPO_TPENBL)
    return state == IO_ON


def is_faulted(self):
    """Determine whether the controller is currently faulted.

    Checks SOP output index 3 (from kliosop.kl).

    :returns: True if there is an active fault on the controller
    :rtype: bool
    """
    state = self.io_read_sopout(idx=kliosop.SOPO_FAULT)
    return state == IO_ON


def is_e_stopped(self):
    """Determine whether the controller is currently e-stopped.

    Checks SOP input index 0 (from kliosop.kl).

    :returns: True if the e-stop is active
    :rtype: bool
    """
    state = self.io_read_sopin(idx=kliosop.SOPI_ESTOP)
    # active low input
    return state == IO_OFF


def in_remote_mode(self):
    """Determine whether the controller is in remote mode.

    Checks SOP output index 0 (from kliosop.kl).

    :returns: True if a program is running.
    :rtype: bool
    """
    state = self.io_read_sopout(idx=kliosop.SOPO_REMOTE)
    return state == IO_ON


def is_program_running(self):
    """Determine whether the controller is executing a program.

    NOTE: this does not check for any specific program, but will return
    True whenever the currently selected program (or any of its children)
    are not PAUSED or ABORTED.

    Checks UOP output index 3 (from kliouop.kl).

    :returns: True if a program is running.
    :rtype: bool
    """
    state = self.io_read_uopout(idx=kliouop.UOPO_PROGRUN)
    return state == IO_ON


def is_program_paused(self):
    """Determine whether there is a paused program on the controller.

    NOTE: this does not check for any specific program, but will return
    True whenever the currently selected program is PAUSED.

    Checks UOP output index 4 (from kliouop.kl).

    :returns: True if a program is paused.
    :rtype: bool
    """
    state = self.io_read_uopout(idx=kliouop.UOPO_PAUSED)
    return state == IO_ON


def list_errors(self):
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
    ftpc = FtpClient(self._host, timeout=self._request_timeout)
    # log in using username and pw, if provided by user
    if self._ftp_auth:
        user, pw = self._ftp_auth
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
            err_level, err_state, = level_state
        else:
            err_level, err_state, = '', level_state[0]
        res.append((int(fields[0]), fields[1], fields[2], fields[3],
                    err_level, err_state))

    return res


def get_active_prog(self):
    varname = '$SHELL_WRK.$ACTIVEPROG'
    ret = self.get_scalar_var(varname=varname)
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_curr_routine(self):
    varname = '$SHELL_WRK.$ROUT_NAME'
    ret = self.get_scalar_var(varname=varname)
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_curr_line(self):
    varname = '$SHELL_WRK.$CURR_LINE'
    ret = self.get_scalar_var(varname=varname)
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return int(ret)


def get_num_groups(self):
    varname = '$SCR.$NUM_GROUP'
    ret = self.get_scalar_var(varname=varname)
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return int(ret)


def get_clock(self):
    """ Return the current date and time on the controller.

    NOTE: this method is rather slow, as it parses a web page.

    NOTE 2: the controller reports time with a resolution of 1 minute.

    :returns: Controller date and time.
    :rtype: datetime.datetime
    """
    ret = self._exec_kcl(cmd='show clock', wait_for_response=True)
    # date & time is on the second line of the output
    stamp = ret.strip().split('\n')[1]
    return datetime.datetime.strptime(stamp, '%d-%b-%y %H:%M')
