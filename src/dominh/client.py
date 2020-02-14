
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


import re
import requests

from . ftp import FtpClient


IO_ON=1
IO_OFF=0

JSON_SUCCESS='success'
JSON_REASON='reason'

HELPER_DEVICE='td:'
HELPER_DIR=''

HLPR_SCALAR_VAR='scalar_var'


class DominhException(Exception):
    pass


class Client(object):
    def __init__(self, host, helper_dev=HELPER_DEVICE, helper_dir=HELPER_DIR, skip_helper_upload=False, request_timeout=5):
        """Initialise an instance of the Dominh Client class.

        # TODO: support authentication

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
        """

        self.host = host
        self.helpers_uploaded = False
        self.skip_helper_upload = skip_helper_upload
        self.request_timeout = request_timeout

        # TODO: do this some other way
        self.base_path = '{}/{}'.format(helper_dev, helper_dir)
        while ('//' in self.base_path):
            self.base_path = self.base_path.replace('//', '/')
        if self.base_path.endswith('/'):
            self.base_path = self.base_path[:-1]


    def __upload_helpers(self, host, remote_path, reupload=False):
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
        ftpc.connect()

        # non array var reader helper
        # this is much faster than downloading and parsing the output of
        # KCL 'SHOW VAR', but should be limited to non-array variables (or
        # individual array elements)
        content = rb'{ "<!-- #ECHO var="_reqvar" -->": "<!-- #ECHO var="{_reqvar}" -->" }'
        ftpc.upload_as_file('/{}/{}.stm'.format(remote_path, HLPR_SCALAR_VAR), content)


    def __get_stm(self, page, params={}):
        """Retrieve a '.stm' file from the controller (rendered by the web server).

        :param page: Location of the stm to retrieve
        :type page: str
        :param params: a dict containing key:value pairs to pass as a query string
        :type params: dict(str:str)
        :returns: JSON response as returned by the controller in its response
        :rtype: dict
        """

        url = 'http://{host}/{base}/{page}'.format(host=self.host, base=self.base_path, page=page)
        r = requests.get(url, params=params, timeout=self.request_timeout)
        if r.status_code != requests.codes.ok:
            raise DominhException("Controller web server returned an "
                "error: {0}".format(r.status_code))
        return r.json()


    def __read_helper(self, helper, params={}):
        """Retrieve JSON from helper on controller.

        NOTE: 'helper' should not include the extension

        :param helper: Name of the helper page (excluding extension)
        :type helper: str
        :param params: a dict containing key:value pairs to pass as a query string
        :type params: dict(str:str)
        :returns: JSON response as returned by the controller in its response
        :rtype: dict
        """

        if not self.helpers_uploaded and not self.skip_helper_upload:
            raise DominhException("Helpers not uploaded")
        if '.stm' in helper.lower():
            raise ValueError("Helper name includes extension")
        return self.__get_stm(page=helper + '.stm', params=params)


    def __exec_kcl(self, cmd, wait_for_response=False):
        """Execute the specified KCL command line on the controller.

        NOTE: any expected parameters must be supplied as part of 'cmd'.

        :param cmd: Valid KCL command (including any required arguments) as a
        single string
        :type cmd: str
        :param wait_for_response: whether or not any output is expected to be
        returned by the server, and whether that output should be captured and
        parsed before being returned to the caller (default: False)
        :type wait_for_response: bool
        :returns: Verbatim copy of the text enclosed in XMP tags, as returned by
        the controller
        :rtype: str
        """

        base = 'KCL' if wait_for_response else 'KCLDO'
        url = 'http://{host}/{base}/{cmd}'.format(host=self.host, base=base, cmd=cmd)
        r = requests.get(url, timeout=self.request_timeout)

        # caller requested we check return value
        if wait_for_response:
            if r.status_code != requests.codes.ok:
                raise DominhException("Unexpected result code. "
                    "Expected: {}, got: {}".format(requests.codes.ok, r.status_code))
            # retrieve KCL command response from doc
            # TODO: could compile these and store them as we might use them more often
            kcl_output = re.search(r'<XMP>(.*)</XMP>', r.text, re.DOTALL)
            if kcl_output:
                return kcl_output.group(1)
            raise DominhException("Could not find KCL output in returned document")

        # if we don't wait, we don't return anything, but we do check the
        # controller returned the appropriate HTTP result code
        if r.status_code != requests.codes.no_content:
            raise DominhException("Unexpected result code. "
                "Expected: {}, got: {}".format(requests.codes.no_content, r.status_code))


    def __exec_karel_prg(self, prg_name, params={}):
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

        url = 'http://{host}/KAREL/{prog}'.format(host=self.host, prog=prg_name)
        r = requests.get(url, params=params, timeout=self.request_timeout)
        if r.status_code != requests.codes.ok:
            raise DominhException("Unexpected result code. "
                "Expected: {}, got: {}".format(requests.codes.ok, r.status_code))
        if 'Unable to run' in r.text:
            raise DominhException("Error: Karel program '{}' cannot"
                " be started on controller.".format(prg_name))
        return r.json()


    def __disable_web_server_headers(self):
        """Prevent Fanuc web server from including headers and footers with each response."""

        self.set_scalar_var('$HTTP_CTRL.$ENAB_TEMPL', 0)


    def __enable_web_server_headers(self):
        """Allow Fanuc web server to include headers and footers with each response."""

        self.set_scalar_var('$HTTP_CTRL.$ENAB_TEMPL', 1)


    def initialise(self):
        """Perform initialisation work needed to use the library.

        In particular: upload the helper scripts and programs to the controller.

        TODO: support authentication somehow.
        """

        if not self.skip_helper_upload:
            self.__upload_helpers(self.host, remote_path=self.base_path)
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

        ret = self.__exec_kcl(cmd='set var {}={}'.format(varname, val))


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

        ret = self.__read_helper(helper=HLPR_SCALAR_VAR, params={'_reqvar':varname})
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

        ret = self.__exec_kcl(cmd='set port {}[{}]={}'.format(port_type, idx, val),
            wait_for_response=check)
        if not check:
            return

        # get some simple errors out of the way
        ret = ret.strip()
        if 'Port name expected' in ret:
            raise DominhException("Illegal port type identifier: '{}'"
                .format(port_type))
        if 'Illegal port number' in ret:
            raise DominhException("Illegal port number for port {}: {}"
                .format(port_type, idx))
        if 'Value out of range' in ret:
            raise DominhException("Value out of range for port type {}: {}"
                .format(port_type, val))
        if 'ERROR' in ret:
            raise DominhException("Unrecognised error trying to set port:\n"
                "\n________________\n\n{}\n________________".format(ret))

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
        port_id = '{}[{}]'.format(port_type, idx)
        ret = self.__read_helper(helper=HLPR_SCALAR_VAR, params={'_reqvar':port_id})

        # check for some common problems
        if 'unknown port type name' in ret[port_id].lower():
            raise DominhException("Illegal port type identifier: '{}'"
                .format(port_type))
        if 'illegal port number' in ret[port_id].lower():
            raise DominhException("Illegal port number for port {}: {}"
                .format(port_type, idx))

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

        self.__exec_kcl(cmd='reset')


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
        ret = self.__exec_karel_prg(prg_name='dmh_selprg', params={'prog_name':program})
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
        ret = self.set_scalar_var(varname, val)


    def get_numreg(self, idx):
        """Retrieve the value stored in the numerical register at 'idx'.

        :param idx: The index of the register to retrieve.
        :type idx: int
        :returns: Either the integer or the floating point number stored at
        index 'idx' in the numerical registers on the controller
        :rtype: int or float (see above)
        """
        varname = '$NUMREG[{}]'.format(idx)
        ret = self.get_scalar_var(varname)
        return float(ret) if '.' in ret else int(ret)


    def list_programs(self, types=[]):
        """Retrieve the list of all programs stored on the controller.

        NOTE: this is a rather naive implementation which should not be used in
        tight loops or when high performance is required.

        :param types: A list of program types to include in the returned result.
        Legal values are those used by the controller when displaying lists of
        programs in the pages served by the Fanuc web server (fi: PC, MACRO, TP,
        VR, etc)
        :type types: list[str]
        :returns: List of tuples containing names and type of programs on the
        controller in the order they are returned
        :rtype: list[tuple(str, str)]
        """
        # TODO: check whether headers are currently enabled and restore state
        # after having used 'show progs'
        self.__disable_web_server_headers()
        # TODO: see whether FTP-ing 'prgstate.dg' would be faster
        ret = self.__exec_kcl(cmd='show progs', wait_for_response=True)
        self.__enable_web_server_headers()

        # parse returned list
        # TODO: we only return '(name, type)' tuples for now
        matches = re.findall(r'(\S+)\s+(\S+)\s+Task', ret.strip(), re.DOTALL)

        types = [t.lower() for t in types]
        return [m for m in matches if (types and m[1].lower() in types) or not types]


    def in_auto_mode(self):
        """Determine whether the controller is in AUTO or one of the MANUAL modes.

        Wraps the Karel IN_AUTO_MODE routine.

        :returns: True if the controller is in AUTO mode
        :rtype: bool
        """

        ret = self.__exec_karel_prg(prg_name='dmh_autom')
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
