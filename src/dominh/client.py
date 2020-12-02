
# Copyright (c) 2020, G.A. vd. Hoorn
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
import requests

from collections import namedtuple

from . ftp import FtpClient


IO_ON = 1
IO_OFF = 0

JSON_SUCCESS = 'success'
JSON_REASON = 'reason'

HELPER_DEVICE = 'td:'
HELPER_DIR = ''

HLPR_RAW_VAR = 'raw_var'
HLPR_SCALAR_VAR = 'scalar_var'


class DominhException(Exception):
    pass


class LockedResourceException(DominhException):
    pass


class AuthenticationException(DominhException):
    pass


Plst_Grp_t = namedtuple('Plst_Grp_t', [
    'comment',
    'payload',
    'payload_x',
    'payload_y',
    'payload_z',
    'payload_ix',
    'payload_iy',
    'payload_iz',
])

Config_t = namedtuple('Config_t', [
    'flip',
    'up',
    'top',
    'turn_no1',
    'turn_no2',
    'turn_no3',
])

Position_t = namedtuple('Position_t', [
    'config',
    'x',
    'y',
    'z',
    'w',
    'p',
    'r',
])

JointPos_t = namedtuple('JointPos_t', [
    'j1',
    'j2',
    'j3',
    'j4',
    'j5',
    'j6',
])


class Client(object):
    def __init__(self, host, helper_dev=HELPER_DEVICE, helper_dir=HELPER_DIR,
                 skip_helper_upload=False, request_timeout=5,
                 kcl_creds=None, karel_creds=None, ftp_creds=None):
        """Initialise an instance of the Dominh Client class.

        Note: use 'skip_helper_upload' to override the default behaviour which
        always uploads the helpers. If they have already been uploaded (for
        instance by a previous or concurrent Client session), avoiding the
        upload could save some seconds during initialisation of this session.

        :param host: Hostname or IP address of the controller
        :type host: str
        :param helper_dev: Device (on controller) that stores the helpers
        (default: 'td:')
        :type helper_dev: str
        :param helper_dir: Path to the directory (on the controller) which
        stores the helpers (default: '' (empty string))
        :type helper_dir: str
        :param skip_helper_upload: Whether or not uploading helpers to the
        controller should skipped (default: False)
        :type skip_helper_upload: bool
        :param request_timeout: Time after which requests should time out
        (default: 5 sec)
        :type request_timeout: float
        :param kcl_creds: A tuple (username, password) providing the
        credentials for access to KCL resources. If not set, the KCL resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource.
        :type kcl_creds: tuple(str, str)
        :param karel_creds: A tuple (username, password) providing the
        credentials for access to Karel resources. If not set, the Karel
        resource is assumed to be accessible by anonymous users and such access
        will fail if the controller does have authentication configured for
        that resource.
        :type karel_creds: tuple(str, str)
        :param ftp_creds: A tuple (username, password) providing the
        credentials for access to FTP resources. If not set, the FTP resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource.
        :type ftp_creds: tuple(str, str)
        """
        self.host = host
        self.helpers_uploaded = False
        self.skip_helper_upload = skip_helper_upload
        self.request_timeout = request_timeout

        # authentication data
        self.kcl_creds = kcl_creds
        self.karel_creds = karel_creds
        self.ftp_creds = ftp_creds

        # TODO: do this some other way
        self.base_path = f'{helper_dev}/{helper_dir}'
        while ('//' in self.base_path):
            self.base_path = self.base_path.replace('//', '/')
        if self.base_path.endswith('/'):
            self.base_path = self.base_path[:-1]

    def _upload_helpers(self, host, remote_path, reupload=False):
        """Upload the (set of) helper(s) files to the controller.

        These helpers are used by the various other functionality provided by
        this class to read and write variables and in general to access
        controller functions.

        :param host: Hostname or IP address of the controller
        :type host: str
        :param remote_path: Location (within the controller's file system) to
        store the helpers at. Note: do not include any forward slash pre- or
        suffixes
        :type remote_path: str
        :param reupload: Whether to force uploading the helpers, even if this
        has been done before by this object (default: False)
        :type reupload: bool
        """
        if self.helpers_uploaded and not reupload:
            return
        ftpc = FtpClient(host, timeout=self.request_timeout)

        # log in using username and pw, if provided by user
        if self.ftp_creds:
            user, pw = self.ftp_creds
            ftpc.connect(user=user, pw=pw)
        else:
            ftpc.connect()

        # non array var reader helper
        # this is much faster than downloading and parsing the output of
        # KCL 'SHOW VAR', but should be limited to non-array variables (or
        # individual array elements)
        content = rb'{ "<!-- #ECHO var="_reqvar" -->": "<!-- #ECHO var="{_reqvar}" -->" }'  # noqa
        ftpc.upload_as_file(f'/{remote_path}/{HLPR_SCALAR_VAR}.stm', content)
        content = rb'<!-- #ECHO var="{_reqvar}" -->'
        ftpc.upload_as_file(f'/{remote_path}/{HLPR_RAW_VAR}.stm', content)

    def _get_stm(self, page, params={}):
        """Retrieve a '.stm' file from the controller (rendered by the web
        server).

        :param page: Location of the stm to retrieve
        :type page: str
        :param params: a dict containing key:value pairs to pass as a query
        string
        :type params: dict(str:str)
        :returns: JSON response as returned by the controller in its response
        :rtype: dict
        """
        url = f'http://{self.host}/{self.base_path}/{page}'
        r = requests.get(url, params=params, timeout=self.request_timeout)
        if r.status_code != requests.codes.ok:
            raise DominhException("Controller web server returned an "
                                  f"error: {r.status_code}")
        return r

    def _read_helper(self, helper, params={}):
        """Retrieve JSON from helper on controller.

        NOTE: 'helper' should not include the extension

        :param helper: Name of the helper page (excluding extension)
        :type helper: str
        :param params: a dict containing key:value pairs to pass as a query
        string
        :type params: dict(str:str)
        :returns: JSON response as returned by the controller in its response
        :rtype: dict
        """
        if not self.helpers_uploaded and not self.skip_helper_upload:
            raise DominhException("Helpers not uploaded")
        if '.stm' in helper.lower():
            raise ValueError("Helper name includes extension")
        return self._get_stm(page=f'{helper}.stm', params=params).json()

    def _exec_kcl(self, cmd, wait_for_response=False):
        """Execute the specified KCL command line on the controller.

        NOTE: any expected parameters must be supplied as part of 'cmd'.

        :param cmd: Valid KCL command (including any required arguments) as a
        single string
        :type cmd: str
        :param wait_for_response: whether or not any output is expected to be
        returned by the server, and whether that output should be captured and
        parsed before being returned to the caller (default: False)
        :type wait_for_response: bool
        :returns: Verbatim copy of the text enclosed in XMP tags, as returned
        by the controller
        :rtype: str
        """
        base = 'KCL' if wait_for_response else 'KCLDO'
        url = f'http://{self.host}/{base}/{cmd}'
        r = requests.get(
            url, auth=self.kcl_creds, timeout=self.request_timeout)

        # always check for authentication issues, even if caller doesn't
        # necessarily want the response checked.
        if r.status_code == requests.codes.unauthorized:
            raise AuthenticationException("Authentication failed (KCL)")
        if r.status_code == requests.codes.forbidden:
            raise LockedResourceException("Access is forbidden/locked (KCL)")

        # if we don't wait, we don't return anything, but we do check the
        # controller returned the appropriate HTTP result code
        if not wait_for_response:
            if r.status_code != requests.codes.no_content:
                raise DominhException(
                    "Unexpected result code. Expected: "
                    f"{requests.codes.no_content}, got: {r.status_code}")

        # caller requested we check return value
        else:
            if r.status_code != requests.codes.ok:
                raise DominhException(
                    f"Unexpected result code. Expected: {requests.codes.ok}, "
                    f"got: {r.status_code}")
            # retrieve KCL command response from doc
            # TODO: could compile these and store them as we might use them
            # more often
            kcl_output = re.search(r'<XMP>(.*)</XMP>', r.text, re.DOTALL)
            if kcl_output:
                return kcl_output.group(1)
            raise DominhException(
                "Could not find KCL output in returned document")

    def _exec_karel_prg(self, prg_name, params={}, return_raw=False):
        """Execute a Karel program on the controller (via the web server).

        NOTE: 'prg_name' should not include the '.pc' extension.

        NOTE 2: this method assumes the Karel program returns JSON. If it does
        not, an exception will be raised by the underlying requests library.

        :param prg_name: Name of the program to execute (excluding extension)
        :type prg_name: str
        :param params: a dict containing key:value pairs to pass as a query
        string, containing arguments the Karel program expects
        :type params: dict(str:str)
        :returns: JSON response sent by the Karel program
        :rtype: str
        """
        if '.pc' in prg_name.lower():
            raise ValueError(f"Program name includes extension ('{prg_name}')")
        url = f'http://{self.host}/KAREL/{prg_name}'
        r = requests.get(url, auth=self.karel_creds, params=params,
                         timeout=self.request_timeout)
        # provide caller with appropriate exceptions
        if r.status_code == requests.codes.unauthorized:
            raise AuthenticationException("Authentication failed (Karel)")
        if r.status_code == requests.codes.forbidden:
            raise LockedResourceException("Access is forbidden/locked (Karel)")
        if r.status_code != requests.codes.ok:
            raise DominhException(
                f"Unexpected result code. Expected: {requests.codes.ok}, "
                f"got: {r.status_code}")
        if 'Unable to run' in r.text:
            raise DominhException(
                f"Error: Karel program '{prg_name}' cannot be started on "
                "controller")
        return r.json() if not return_raw else r.text

    def _disable_web_server_headers(self):
        """Prevent Fanuc web server from including headers and footers with
        each response.
        """
        self.set_scalar_var('$HTTP_CTRL.$ENAB_TEMPL', 0)

    def _enable_web_server_headers(self):
        """Allow Fanuc web server to include headers and footers with each
        response.
        """
        self.set_scalar_var('$HTTP_CTRL.$ENAB_TEMPL', 1)

    def initialise(self):
        """Perform initialisation work needed to use the library.

        In particular: upload the helper scripts and programs to the
        controller.

        TODO: support authentication somehow.
        """
        if not self.skip_helper_upload:
            self._upload_helpers(self.host, remote_path=self.base_path)
            # if we get here, we assume the following to be True
            # TODO: verify
            self.helpers_uploaded = True

    def set_scalar_var(self, varname, val):
        """Update the value of variable 'varname' to 'val'.

        NOTE: 'val' will always be sent as its 'str(..)'-i-fied representation.
        The controller will (attempt to) parse this back into its native data
        type.

        TODO: add basic error checking (none performed right now).

        :param varname: Name of the variable to write to
        :type varname: str
        :param val: Value to write to 'varname'
        :type val: any (must have str() support)
        """
        self._exec_kcl(cmd=f'set var {varname}={val}')

    def get_scalar_var(self, varname):
        """Retrieve the value of the variable named 'varname'.

        NOTE: should only be used for scalar variables and individual array
        elements.

        TODO: see whether perhaps SHOW VAR could be used here instead.

        :param varname: Name of the variable to write to
        :type varname: str
        :returns: JSON value for key 'varname'
        :rtype: str (to be parsed by caller)
        """
        ret = self._read_helper(
            helper=HLPR_SCALAR_VAR, params={'_reqvar': varname})
        return ret[varname.upper()]

    def io_write(self, port_type, idx, val, check=False):
        """Set port 'idx' of type 'port_type' to value 'val'.

        Valid values for 'port_type':

          BOOLEAN:
         -  DIN
         -  DOUT
         -  RDO
         -  OPOUT
         -  TPOUT
         -  WDI
         -  WDO
          INTEGER:
         -  AIN
         -  AOUT
         -  GIN
         -  GOUT

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
        ret = self._exec_kcl(
            cmd=f'set port {port_type}[{idx}]={val}', wait_for_response=check)
        if not check:
            return

        # get some simple errors out of the way
        ret = ret.strip()
        if 'Port name expected' in ret:
            raise DominhException(
                f"Illegal port type identifier: '{port_type}'")
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

    def io_write_dout(self, idx, val):
        """Write 'val' to 'DOUT[idx]'.

        :param idx: Index to write to
        :type idx: int
        :param val: Value to write
        :type val: int
        """
        self.io_write('DOUT', idx, val)

    def io_write_rout(self, idx, val):
        """Write 'val' to 'ROUT[idx]'.

        :param idx: Index to write to
        :type idx: int
        :param val: Value to write
        :type val: int
        """
        self.io_write('ROUT', idx, val)

    def io_read(self, port_type, idx):
        """Read port 'idx' of type 'port_type'.

        Valid values for 'port_type':

          BOOLEAN:
            BRAKE
            DIN
            DOUT
            ESTOP
            LDIN
            LDOUT
            PLCIN
            PLCOUT
            RDI
            RDO
            SOPIN
            SOPOUT
            TOOL
            TPIN
            TPOUT
            UOPIN
            UOPOUT
            WDI
            WDO
            WSIN
            WSOUT
          INTEGER:
            ANIN
            ANOUT
            GPIN
            GPOUT
            LANIN
            LANOUT

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
        ret = self._read_helper(
            helper=HLPR_SCALAR_VAR, params={'_reqvar': port_id})

        # check for some common problems
        if 'unknown port type name' in ret[port_id].lower():
            raise DominhException(
                f"Illegal port type identifier: '{port_type}'")
        if 'illegal port number' in ret[port_id].lower():
            raise DominhException(
                f"Illegal port number for port {port_type}: {idx}")

        return ret[port_id]

    def io_read_sopout(self, idx):
        """Read from 'SOPOUT[idx]'.

        :param idx: Index to read from
        :type idx: int
        :returns: Current state of 'SOPOUT[idx]'
        :rtype: int
        """
        return IO_ON if self.io_read('SOPOUT', idx) == 'ON' else IO_OFF

    def io_read_uopout(self, idx):
        """Read from 'UOPOUT[idx]'.

        :param idx: Index to read from
        :type idx: int
        :returns: Current state of 'UOPOUT[idx]'
        :rtype: int
        """
        return IO_ON if self.io_read('UOPOUT', idx) == 'ON' else IO_OFF

    def io_read_rout(self, idx):
        """Read from 'RDO[idx]'.

        :param idx: Index to write to
        :type idx: int
        :returns: Current state of 'RDO[idx]'
        :rtype: int
        """
        return IO_ON if self.io_read('RDO', idx) == 'ON' else IO_OFF

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
        # from kliosop
        SOPO_TPENBL = 7
        state = self.io_read_sopout(idx=SOPO_TPENBL)
        return state == IO_ON

    def is_faulted(self):
        """Determine whether the controller is currently faulted.

        Checks SOP output index 3 (from kliosop.kl).

        :returns: True if there is an active fault on the controller
        :rtype: bool
        """
        # from kliosop
        SOPO_FAULT = 3
        state = self.io_read_sopout(idx=SOPO_FAULT)
        return state == IO_ON

    def is_e_stopped(self):
        """Determine whether the controller is currently e-stopped.

        Checks SOP input index 0 (from kliosop.kl).

        :returns: True if the e-stop is active
        :rtype: bool
        """
        # from kliosop
        SOPI_ESTOP = 0
        state = self.io_read_sopout(idx=SOPI_ESTOP)
        return state == IO_ON

    def in_remote_mode(self):
        """Determine whether the controller is in remote mode.

        Checks SOP output index 0 (from kliosop.kl).

        :returns: True if a program is running.
        :rtype: bool
        """
        # from kliosop
        SOPO_REMOTE = 0
        state = self.io_read_sopout(idx=SOPO_REMOTE)
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
        # from kliouop
        UOPO_PROGRUN = 3
        state = self.io_read_uopout(idx=UOPO_PROGRUN)
        return state == IO_ON

    def is_program_paused(self):
        """Determine whether there is a paused program on the controller.

        NOTE: this does not check for any specific program, but will return
        True whenever the currently selected program is PAUSED.

        Checks UOP output index 4 (from kliouop.kl).

        :returns: True if a program is paused.
        :rtype: bool
        """
        # from kliouop
        UOPO_PAUSED = 4
        state = self.io_read_uopout(idx=UOPO_PAUSED)
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
        ftpc = FtpClient(self.host, timeout=self.request_timeout)
        # log in using username and pw, if provided by user
        if self.ftp_creds:
            user, pw = self.ftp_creds
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

    def _get_cmt_fc(self, cmt):
        return {
            'NUMREG': 1,
            'POSREG': 3,
            'UALARM': 4,
            'RDI': 6,
            'RDO': 7,
            'DIN': 8,
            'DOUT': 9,
            'GIN': 10,
            'GOUT': 11,
            'AIN': 12,
            'AOUT': 13,
            'STRREG': 14,
            'FLG': 19,
        }.get(cmt.upper())

    def _get_val_fc(self, valt):
        return {
            'NUMREG': 2,
            'UALARM': 5,  # actually sets 'severity'
            'STRREG': 15,
        }.get(valt.upper())

    def _comset(self, fc, idx, val=None, comment=''):
        """Low-level wrapper around the 'karel/ComSet' program.

        This method uses the COMSET Karel program on the controller, which is
        normally used by the 'Comment Tool' (accessible via the controller's
        web server).

        Valid values for 'fc':

        When updating a comment:

         - AIN
         - AOUT
         - DIN
         - DOUT
         - FLG
         - GIN
         - GOUT
         - NUMREG
         - POSREG
         - RDI
         - RDO
         - STRREG
         - UALARM

        When updating a value:

         - NUMREG
         - STRREG
         - UALARM

        Note: if both 'val' and 'comment' are set, only the comment will be
        updated on the controller.

        :param fc: Type name of commentable
        :type fc: str
        :param idx: Numeric ID of register/alarm/IO element
        :type idx: int
        :param val: Value to write to register
        :type val: int/float/str
        :param comment: Comment to set on commentable
        :type comment: str
        """
        if not val and not comment:
            raise ValueError("Need either val or comment")

        if val:
            sfc = self._get_val_fc(fc)
            real_flag = 1 if type(val) == float else -1
            params = {
                'sValue': val,
                'sIndx': idx,
                'sRealFlag': real_flag,
                'sFc': sfc
            }

        if comment:
            sfc = self._get_cmt_fc(fc)
            params = {
                'sComment': comment,
                'sIndx': idx,
                'sFc': sfc
            }

        # make sure to request 'return_raw', as 'ComSet' does not return JSON
        # TODO: check return value
        self._exec_karel_prg(
            prg_name='ComSet', params=params, return_raw=True)

    def cmt_numreg(self, idx, comment):
        """Update the comment on numerical register at 'idx'.

        :param idx: Numeric ID of register
        :type idx: int
        :param comment: Comment to set
        :type comment: str
        """
        self._comset('NUMREG', idx, comment=comment)

    def cmt_posreg(self, idx, comment):
        """Update the comment on position register at 'idx'.

        :param idx: Numeric ID of register
        :type idx: int
        :param comment: Comment to set
        :type comment: str
        """
        self._comset('POSREG', idx, comment=comment)

    def cmt_din(self, idx, comment):
        """Update the comment on 'DIN[idx]'.

        :param idx: Numeric ID of port
        :type idx: int
        :param comment: Comment to set
        :type comment: str
        """
        self._comset('DIN', idx, comment=comment)

    def cmt_dout(self, idx, comment):
        """Update the comment on 'DOUT[idx]'.

        :param idx: Numeric ID of port
        :type idx: int
        :param comment: Comment to set
        :type comment: str
        """
        self._comset('DOUT', idx, comment=comment)

    def get_strreg(self, idx):
        """Retrieve the value stored in the string register at 'idx'.

        :param idx: The index of the register to retrieve.
        :type idx: int
        :returns: The string stored at index 'idx' in the string registers on
        the controller
        :rtype: str
        """
        # TODO: rather nasty hard-coded variable name
        # TODO: check for errors (fi idx too high)
        varname = f'[*STRREG*]$STRREG[{idx}]'
        ret = self.get_scalar_var(varname)
        return ret

    def get_num_strreg(self):
        """Retrieve total number of string registers available on the
        controller.

        :returns: value of [*STRREG*]$MAXSREGNUM.
        :rtype: int
        """
        ret = self.get_scalar_var('[*STRREG*]$MAXSREGNUM')
        return int(ret)

    def get_numreg(self, idx):
        """Retrieve the value stored in the numerical register at 'idx'.

        :param idx: The index of the register to retrieve.
        :type idx: int
        :returns: Either the integer or the floating point number stored at
        index 'idx' in the numerical registers on the controller
        :rtype: int or float (see above)
        """
        varname = f'$NUMREG[{idx}]'
        ret = self.get_scalar_var(varname)
        return float(ret) if '.' in ret else int(ret)

    def set_numreg(self, idx, val):
        """Update the value stored in 'R[idx]' to 'val'.

        Note: 'val' must be either int or float.

        :param idx: The index of the register to update
        :type idx: int
        :param val: The value to write to the register
        :type val: int or float
        """
        assert type(val) in [float, int]
        self._comset('NUMREG', idx, val=val)

    def _format_sysvar(self, path):
        assert type(path) == list
        if not path:
            raise ValueError("Need at least one variable name")
        return ('$' + '.$'.join(path)).upper()

    def get_payload(self, idx, grp=1):
        """Retrieve payload nr 'idx' for group 'grp'.

        NOTE: this method is expensive and slow, as it retrieves the individual
        fields of the payload variable separately, instead of a single struct.

        :param idx: The number of the payload schedule to retrieve
        :type idx: int
        :param grp: The motion group to retrieve the payload for
        :type grp: int
        :returns: A named tuple matching the structure of a PLST_GRP_T. The
        'ICONDISP' field is not included.
        :rtype: plst_grp_t
        """
        if (grp < 1 or grp > 5):
            raise ValueError(f"Group ID must be between 1 and 5 (got: {grp})")
        if (idx < 1 or idx > 10):
            raise ValueError(
                f"Payload ID must be between 1 and 10 (got: {idx})")

        # TODO: retrieve struct in one read and parse result instead
        base_vname = f'plst_grp{grp}[{idx}]'
        cmt = self.get_scalar_var(
                self._format_sysvar([base_vname, 'comment']))
        return Plst_Grp_t(
            comment=None if cmt == 'Uninitialized' else cmt,
            payload=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload']))),
            payload_x=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_x']))),
            payload_y=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_y']))),
            payload_z=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_z']))),
            payload_ix=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_ix']))),
            payload_iy=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_iy']))),
            payload_iz=float(self.get_scalar_var(
                self._format_sysvar([base_vname, 'payload_iz']))),
        )

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

    def _match_position(self, text):
        """Try to extract elements of a FANUC POSITION from 'text'.

        :param text: Textual representation of a POSITION variable.
        :type text: str
        :returns: A tuple with all the matched fields.
        :rtype: tuple(str, str, ..)
        """
        # use Jay's regex (thanks!)
        matches = re.findall(
            r"(?m)"
            r"("
            r"  Group: (\d)   Config: (F|N) (U|D) (T|B), (\d), (\d), (\d)\r?\n"
            r"  X:\s*(-?\d*.\d+|[*]+)   Y:\s+(-?\d*.\d+|[*]+)   Z:\s+(-?\d*.\d+|[*]+)\r?\n"  # noqa
            r"  W:\s*(-?\d*.\d+|[*]+)   P:\s*(-?\d*.\d+|[*]+)   R:\s*(-?\d*.\d+|[*]+)"  # noqa
            r"|"
            r"  Group: (\d)\r?\n"
            r"  (J1) =\s*(-?\d*.\d+|[*]+) deg   J2 =\s*(-?\d*.\d+|[*]+) deg   J3 =\s*(-?\d*.\d+|[*]+) deg \r?\n"  # noqa
            r"  J4 =\s*(-?\d*.\d+|[*]+) deg   J5 =\s*(-?\d*.\d+|[*]+) deg   J6 =\s*(-?\d*.\d+|[*]+) deg"  # noqa
            r")",
            text)
        return matches[0] if matches else None

    def _get_var_raw(self, varname):
        """Retrieve raw text dump of variable with name 'varname'.

        :param varname: Name of the variable to retrieve.
        :type varname: str
        :returns: Raw textual rendering of the (system) variable 'varname'.
        :rtype: str
        """
        # use get_stm(..) directly here as what we get returned is not actually
        # json, and read_helper(..) will try to parse it as such and then fail
        ret = self._get_stm(
            page=HLPR_RAW_VAR + '.stm', params={'_reqvar': varname})
        return ret.text

    def _get_frame_var(self, varname):
        """Retrieve the POSITION variable 'varname'.

        :param varname: Name of the variable to retrieve.
        :type varname: str
        :returns: Position_t instance populated with values retrieved from the
        'varname' variable.
        :rtype: Position_t
        """
        # NOTE: assuming here that get_var_raw(..) returns something we can
        # actually parse
        ret = self._get_var_raw(varname)
        # remove the first line as it's empty
        match = self._match_position(ret.replace('\r\n', '', 1))

        if not match:
            raise DominhException(
                f"Could not match value returned for '{varname}'")

        # some nasty fiddling
        # TODO: this won't work for non-6-axis systems
        f = match[2] == 'F'  # N
        u = match[3] == 'U'  # D
        t = match[4] == 'T'  # B
        turn_nos = list(map(int, match[5:8]))
        xyzwpr = list(map(float, match[8:14]))
        return Position_t(Config_t(f, u, t, *turn_nos), *xyzwpr)

    def _get_frame_comment(self, frame_type, group, idx):
        """Return the comment for the jog/tool/user frame 'idx'.

        :param frame_type: Type of frame the comment is associated with (
        jog:2, tool:1, user:3).
        :type frame_type: int
        :param group: Numeric ID of the motion group the frame is associated
        with.
        :type group: int
        :param idx: Numeric ID of the frame.
        :type idx: int
        :returns: The comment of the frame in group 'group', with ID 'idx'
        :rtype: str
        """
        varname = f'[TPFDEF]SETUP_DATA[{group},{frame_type},{idx}].$COMMENT'
        return self.get_scalar_var(varname)

    def get_jogframe(self, idx, group=1, include_comment=False):
        """Return the jog frame at index 'idx'.

        :param idx: Numeric ID of the jog frame.
        :type idx: int
        :param group: Numeric ID of the motion group the jog frame is
        associated with.
        :type group: int
        :returns: A tuple containing the user frame and associated comment (if
        requested)
        :rtype: tuple(Position_t, str)
        """
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        if idx < 1 or idx > 5:
            raise ValueError("Requested jog frame idx invalid (must be "
                             f"between 1 and 5, got: {idx})")
        varname = f'[TPFDEF]JOGFRAMES[{group},{idx}]'
        frame = self._get_frame_var(varname)
        cmt = None
        if include_comment:
            JOGFRAME = 2
            cmt = self._get_frame_comment(
                frame_type=JOGFRAME, group=group, idx=idx)
        return (frame, cmt)

    def get_toolframe(self, idx, group=1, include_comment=False):
        """Return the tool frame at index 'idx'.

        :param idx: Numeric ID of the tool frame.
        :type idx: int
        :param group: Numeric ID of the motion group the tool frame is
        associated with.
        :type group: int
        :returns: A tuple containing the tool frame and associated comment (if
        requested)
        :rtype: tuple(Position_t,) or tuple(Position_t, str)
        """
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        if idx < 1 or idx > 10:
            raise ValueError("Requested tool frame idx invalid (must be "
                             f"between 1 and 10, got: {idx})")
        varname = f'[*SYSTEM*]$MNUTOOL[{group},{idx}]'
        frame = self._get_frame_var(varname)
        cmt = None
        if include_comment:
            TOOLFRAME = 1
            cmt = self._get_frame_comment(
                frame_type=TOOLFRAME, group=group, idx=idx)
        return (frame, cmt)

    def get_userframe(self, idx, group=1, include_comment=False):
        """Return the user frame at index 'idx'.

        :param idx: Numeric ID of the user frame.
        :type idx: int
        :param group: Numeric ID of the motion group the user frame is
        associated with.
        :type group: int
        :returns: A tuple containing the user frame and associated comment (if
        requested)
        :rtype: tuple(Position_t, str)
        """
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        if idx < 1 or idx > 10:
            raise ValueError("Requested user frame idx invalid (must be "
                             f"between 1 and 10, got: {idx})")
        varname = f'[*SYSTEM*]$MNUFRAME[{group},{idx}]'
        frame = self._get_frame_var(varname)
        cmt = None
        if include_comment:
            USERFRAME = 3
            cmt = self._get_frame_comment(
                frame_type=USERFRAME, group=group, idx=idx)
        return (frame, cmt)

    def get_active_jogframe(self, group=1):
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        return self.get_scalar_var(varname=f'[TPFDEF]JOGFRAMNUM[{group}]')

    def get_active_toolframe(self, group=1):
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        return self.get_scalar_var(varname=f'[*SYSTEM*]$MNUTOOLNUM[{group}]')

    def get_active_userframe(self, group=1):
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        return self.get_scalar_var(varname=f'[*SYSTEM*]$MNUFRAMENUM[{group}]')

    def get_posreg(self, idx, group=1):
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
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        varname = f'$POSREG[{group},{idx}]'
        # use get_stm(..) directly here as what we get returned is not actually
        # json, and read_helper(..) will try to parse it as such and then fail
        ret = self._get_stm(
            page=HLPR_RAW_VAR + '.stm', params={'_reqvar': varname})

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
            ret.text)

        if not match:
            raise DominhException(
                f"Could not match value returned for '{varname}'")

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

    def was_jogged(self, group=1):
        if group < 1 or group > 8:
            raise ValueError("Requested group id invalid (must be "
                             f"between 1 and 8, got: {group})")
        varname = f'$MOR_GRP[{group}].$JOGGED'
        ret = self.get_scalar_var(varname=varname)
        if 'bad variable' in ret.lower():
            raise DominhException(f"Could not read sysvar: '{ret}'")
        return ret.lower() == 'true'

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

    def get_robot_id(self, group=1):
        varname = f'$SCR_GRP[{group}].$ROBOT_ID'
        ret = self.get_scalar_var(varname=varname)
        if 'bad variable' in ret.lower():
            raise DominhException(f"Could not read sysvar: '{ret}'")
        return ret

    def get_robot_model(self, group=1):
        varname = f'$SCR_GRP[{group}].$ROBOT_MODEL'
        ret = self.get_scalar_var(varname=varname)
        if 'bad variable' in ret.lower():
            raise DominhException(f"Could not read sysvar: '{ret}'")
        return ret

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
