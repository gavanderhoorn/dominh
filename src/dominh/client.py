
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

from . constants import HELPER_DEVICE
from . constants import HELPER_DIR
from . constants import HLPR_RAW_VAR
from . constants import HLPR_SCALAR_VAR
from . constants import IO_OFF
from . constants import IO_ON
from . constants import JSON_REASON
from . constants import JSON_SUCCESS

from . exceptions import AuthenticationException
from . exceptions import DominhException
from . exceptions import LockedResourceException

from . ftp import FtpClient

from . import kliosop
from . import kliouop

from . types import Config_t
from . types import JointPos_t
from . types import Plst_Grp_t
from . types import Position_t


class Client(object):
    def __init__(self, host, helper_dev=HELPER_DEVICE, helper_dir=HELPER_DIR,
                 skip_helper_upload=False, request_timeout=5,
                 kcl_auth=None, karel_auth=None, ftp_auth=None):
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
        :param kcl_auth: A tuple (username, password) providing the
        credentials for access to KCL resources. If not set, the KCL resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource.
        :type kcl_auth: tuple(str, str)
        :param karel_auth: A tuple (username, password) providing the
        credentials for access to Karel resources. If not set, the Karel
        resource is assumed to be accessible by anonymous users and such access
        will fail if the controller does have authentication configured for
        that resource.
        :type karel_auth: tuple(str, str)
        :param ftp_auth: A tuple (username, password) providing the
        credentials for access to FTP resources. If not set, the FTP resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource.
        :type ftp_auth: tuple(str, str)
        """
        self._host = host
        self._helpers_uploaded = False
        self._skip_helper_upload = skip_helper_upload
        self._request_timeout = request_timeout

        # authentication data
        self._kcl_auth = kcl_auth
        self._karel_auth = karel_auth
        self._ftp_auth = ftp_auth

        # TODO: do this some other way
        self._base_path = f'{helper_dev}/{helper_dir}'
        while ('//' in self._base_path):
            self._base_path = self._base_path.replace('//', '/')
        if self._base_path.endswith('/'):
            self._base_path = self._base_path[:-1]

    def initialise(self):
        """Perform initialisation work needed to use the library.

        In particular: upload the helper scripts and programs to the
        controller.
        """
        if not self._skip_helper_upload:
            self._upload_helpers(self._host, remote_path=self._base_path)
            # if we get here, we assume the following to be True
            # TODO: verify
            self._helpers_uploaded = True
