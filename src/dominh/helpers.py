
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
import requests

from . constants import HLPR_RAW_VAR
from . constants import HLPR_SCALAR_VAR
from . exceptions import AuthenticationException
from . exceptions import DominhException
from . exceptions import LockedResourceException
from . ftp import FtpClient


def upload_helpers(host, remote_path, request_timeout=5, ftp_auth=None):
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
    ftpc = FtpClient(host, timeout=request_timeout)

    # log in using username and pw, if provided by user
    if ftp_auth:
        user, pw = ftp_auth
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


def get_stm(conx, page, params={}):
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
    url = f'http://{conx.host}/{conx.base_path}/{page}'
    r = requests.get(url, params=params, timeout=conx.request_timeout)
    if r.status_code != requests.codes.ok:
        raise DominhException(
            f"Controller web server returned an error: {r.status_code}")
    return r


def read_helper(conx, helper, params={}):
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
    if not conx.helpers_uploaded and not conx.skipped_helpers_upload:
        raise DominhException("Helpers not uploaded")
    if '.stm' in helper.lower():
        raise ValueError("Helper name includes extension")
    return get_stm(conx, page=f'{helper}.stm', params=params).json()


def exec_kcl(conx, cmd, wait_for_response=False):
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
    url = f'http://{conx.host}/{base}/{cmd}'
    r = requests.get(url, auth=conx.kcl_auth, timeout=conx.request_timeout)

    # always check for authentication issues, even if caller doesn't
    # necessarily want the response checked.
    if r.status_code == requests.codes.unauthorized:
        raise AuthenticationException(
            "Authentication failed (KCL). "
            "Are the username and password correct?"
        )
    if r.status_code == requests.codes.forbidden:
        raise LockedResourceException(
            "Access is forbidden/locked (KCL). Please check the 'Host Comm' "
            "configuration on the teach pendant."
        )

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
        raise DominhException("Could not find KCL output in returned document")


def exec_karel_prg(conx, prg_name, params={}, return_raw=False):
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
    url = f'http://{conx.host}/KAREL/{prg_name}'
    r = requests.get(
        url, auth=conx.karel_auth, params=params, timeout=conx.request_timeout)
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


def get_var_raw(conx, varname):
    """Retrieve raw text dump of variable with name 'varname'.

    :param varname: Name of the variable to retrieve.
    :type varname: str
    :returns: Raw textual rendering of the (system) variable 'varname'.
    :rtype: str
    """
    # use get_stm(..) directly here as what we get returned is not actually
    # json, and read_helper(..) will try to parse it as such and then fail
    ret = get_stm(
        conx, page=HLPR_RAW_VAR + '.stm', params={'_reqvar': varname})
    return ret.text
