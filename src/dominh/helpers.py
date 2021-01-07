
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
    if self._helpers_uploaded and not reupload:
        return
    ftpc = FtpClient(host, timeout=self._request_timeout)

    # log in using username and pw, if provided by user
    if self._ftp_auth:
        user, pw = self._ftp_auth
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
    url = f'http://{self._host}/{self._base_path}/{page}'
    r = requests.get(url, params=params, timeout=self._request_timeout)
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
    if not self._helpers_uploaded and not self._skip_helper_upload:
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
    url = f'http://{self._host}/{base}/{cmd}'
    r = requests.get(
        url, auth=self._kcl_auth, timeout=self._request_timeout)

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
    url = f'http://{self._host}/KAREL/{prg_name}'
    r = requests.get(url, auth=self._karel_auth, params=params,
                        timeout=self._request_timeout)
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
