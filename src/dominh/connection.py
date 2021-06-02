# Copyright (c) 2020-2021, G.A. vd. Hoorn
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


import typing as t


class Connection(object):
    def __init__(
        self,
        host: str,
        base_path: str,
        helpers_uploaded: bool,
        skipped_helpers_upload: bool,
        request_timeout: float = 5,
        kcl_auth: t.Optional[t.Tuple[str, str]] = None,
        karel_auth: t.Optional[t.Tuple[str, str]] = None,
        ftp_auth: t.Optional[t.Tuple[str, str]] = None,
    ) -> None:
        """Stores information about an active connection.

        :param host: Hostname or IP address of the controller
        :type host: str
        :param base_path: Path to the directory (on the controller) which
        stores the helpers
        :type base_path: str
        :param helpers_uploaded: Whether or not the helpers were uploaded to
        the controller as part of the initialisation of this connection
        :type helpers_uploaded: bool
        :param skipped_helpers_upload: Whether or not skipping upload of the
        helpers was requested (because they were uploaded as part of
        initialisation of a prior session for instance)
        :type skipped_helpers_upload: bool
        :param request_timeout: Time after which requests should time out
        (default: 5 sec)
        :type request_timeout: float
        :param kcl_auth: A tuple (username, password) providing the
        credentials for access to KCL resources. If not set, the KCL resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource. Default: None
        :type kcl_auth: tuple(str, str)
        :param karel_auth: A tuple (username, password) providing the
        credentials for access to Karel resources. If not set, the Karel
        resource is assumed to be accessible by anonymous users and such access
        will fail if the controller does have authentication configured for
        that resource. Default: None
        :type karel_auth: tuple(str, str)
        :param ftp_auth: A tuple (username, password) providing the
        credentials for access to FTP resources. If not set, the FTP resource
        is assumed to be accessible by anonymous users and such access will
        fail if the controller does have authentication configured for that
        resource. Default: None
        :type ftp_auth: tuple(str, str)
        """

        # which remote system are we connected to?
        self._host = host
        # where are the helpers stored?
        self._base_path = base_path
        # have the helpers been uploaded?
        self._helpers_uploaded = helpers_uploaded
        # were we asked not to upload the helpers?
        self._skipped_helpers_upload = skipped_helpers_upload
        # when should we consider a request to have timed-out?
        self._request_timeout = request_timeout

        # authentication data
        self._kcl_auth = kcl_auth
        self._karel_auth = karel_auth
        self._ftp_auth = ftp_auth

    @property
    def host(self) -> str:
        """Hostname or IP address of the controller"""
        return self._host

    @property
    def base_path(self) -> str:
        """Path to the directory (on the controller) which stores the helpers"""
        return self._base_path

    @property
    def request_timeout(self) -> float:
        """Time after which requests should time out"""
        return self._request_timeout

    @property
    def helpers_uploaded(self) -> bool:
        """Whether or not the helpers were uploaded to the controller as part
        of the initialisation of this connection
        """
        return self._helpers_uploaded

    @property
    def skipped_helpers_upload(self) -> bool:
        """Whether or not skipping upload of the helpers was requested

        Because they were uploaded as part of initialisation of a prior session
        for instance.
        """
        return self._skipped_helpers_upload

    @property
    def kcl_auth(self) -> t.Optional[t.Tuple[str, str]]:
        """Credentials allowing access to KCL resources

        If not provided, returns None.
        """
        return self._kcl_auth

    @property
    def karel_auth(self) -> t.Optional[t.Tuple[str, str]]:
        """Credentials allowing access to Karel resources

        If not provided, returns None.
        """
        return self._karel_auth

    @property
    def ftp_auth(self) -> t.Optional[t.Tuple[str, str]]:
        """Credentials allowing access to FTP resources

        If not provided, returns None.
        """
        return self._ftp_auth
