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


import datetime

from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from .exceptions import DominhException
from .exceptions import UnsupportedVariableTypeException
from .helpers import upload_helpers

from . import comments
from . import controller
from . import frames
from . import group
from . import io
from . import registers
from . import variables


__all__ = ["connect", "DominhException"]


class Connection(object):
    def __init__(
        self,
        host: str,
        base_path: str,
        helpers_uploaded: bool,
        skipped_helpers_upload: bool,
        request_timeout: float = 5,
        kcl_auth: Optional[Tuple[str, str]] = None,
        karel_auth: Optional[Tuple[str, str]] = None,
        ftp_auth: Optional[Tuple[str, str]] = None,
    ):
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
    def kcl_auth(self) -> Optional[Tuple[str, str]]:
        """Credentials allowing access to KCL resources

        If not provided, returns None.
        """
        return self._kcl_auth

    @property
    def karel_auth(self) -> Optional[Tuple[str, str]]:
        """Credentials allowing access to Karel resources

        If not provided, returns None.
        """
        return self._karel_auth

    @property
    def ftp_auth(self) -> Optional[Tuple[str, str]]:
        """Credentials allowing access to FTP resources

        If not provided, returns None.
        """
        return self._ftp_auth


class NumReg(object):
    def __init__(self, conx: Connection, idx: int):
        self._conx = conx
        self._idx = idx

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def val(self) -> int:
        """Returns the current value stored in the numreg at 'idx'"""
        return registers.get_numreg(self._conx, self._idx)

    @val.setter
    def val(self, val: int) -> None:
        """Sets the numreg at 'idx' to 'val'"""
        # TODO: should 'val' be bounds checked? We do know max values it can
        # take (32bit signed integer, 32bit float)
        registers.set_numreg(self._conx, self._idx, val)

    def reset(self, def_val: int = 0) -> None:
        """Resets the numreg at 'idx' to a default value (default: 0)"""
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on NumRegs (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        """Makes the comment on the numreg at 'idx' equal to 'cmt'"""
        comments.cmt_numreg(self._conx, self._idx, cmt)


class StrReg(object):
    def __init__(self, conx: Connection, idx: int):
        self._conx = conx
        self._idx = idx

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def val(self) -> str:
        """Returns the current value stored in the strreg at 'idx'"""
        return registers.get_strreg(self._conx, self._idx)

    @val.setter
    def val(self, val: str) -> None:
        raise NotImplementedError("Can't write to StrRegs (yet)")

    def reset(self, def_val: str = '') -> None:
        """Resets the strreg at 'idx' to a default value (default: '')"""
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on StrRegs (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        raise NotImplementedError("Can't set comments on StrRegs (yet)")


class PosReg(object):
    def __init__(self, conx: Connection, idx: int):
        self._conx = conx
        self._idx = idx

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def val(self):
        """Returns the current value stored in the posreg at 'idx'"""
        return registers.get_posreg(self._conx, self._idx)

    @val.setter
    def val(self, val) -> int:
        raise NotImplementedError("Can't write to PosRegs (yet)")

    def reset(self, def_val=[0.0] * 6) -> None:
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on PosRegs (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        """Makes the comment on the posreg at 'idx' equal to 'cmt'"""
        comments.cmt_posreg(self._conx, self._idx, cmt)


class ToolFrame(object):
    def __init__(self, conx: Connection, idx: int, group: int = 1):
        self._conx = conx
        self._idx = idx
        self._group = group

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def group(self) -> int:
        """Returns the motion group this toolframe is associated with"""
        return self._group

    @property
    def val(self):
        """Returns the toolframe at index 'idx' for group 'group'"""
        return frames.get_toolframe(self._conx, self._idx, self._group)

    @val.setter
    def val(self, val) -> None:
        raise NotImplementedError("Can't write to ToolFrames (yet)")

    def reset(self, def_val=[0.0] * 6) -> None:
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on ToolFrames (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        raise NotImplementedError("Can't set comments on ToolFrames (yet)")


class JogFrame(object):
    def __init__(self, conx: Connection, idx: int, group: int = 1):
        self._conx = conx
        self._idx = idx
        self._group = group

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def group(self) -> int:
        """Returns the motion group this jogframe is associated with"""
        return self._group

    @property
    def val(self):
        """Returns the jogframe at index 'idx' for group 'group'"""
        return frames.get_jogframe(self._conx, self._idx, self._group)

    @val.setter
    def val(self, val) -> None:
        raise NotImplementedError("Can't write to JogFrames (yet)")

    def reset(self, def_val=[0.0] * 6) -> None:
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on JogFrames (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        raise NotImplementedError("Can't set comments on JogFrames (yet)")


class UserFrame(object):
    def __init__(self, conx: Connection, idx: int, group: int = 1):
        self._conx = conx
        self._idx = idx
        self._group = group

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def group(self) -> int:
        """Returns the motion group this userframe is associated with"""
        return self._group

    @property
    def val(self):
        """Returns the userframe at index 'idx' for group 'group'"""
        return frames.get_userframe(self._conx, self._idx, self._group)

    @val.setter
    def val(self, val) -> None:
        raise NotImplementedError("Can't write to UserFrames (yet)")

    def reset(self, def_val=[0.0] * 6) -> None:
        self.val = def_val

    @property
    def cmt(self) -> str:
        raise NotImplementedError("Can't retrieve comments on UserFrames (yet)")

    @cmt.setter
    def cmt(self, cmt: str) -> None:
        raise NotImplementedError("Can't set comments on UserFrames (yet)")


class MotionGroup(object):
    def __init__(self, conx: Connection, id):
        self._conx = conx
        self._id = id

    @property
    def id(self) -> int:
        """Returns the id of this group.

        Note: id != index in the system variables. Group 3 could have index 2
        for instance.
        """
        return self._id

    @property
    def robot_id(self) -> str:
        """Returns the robot model ID for which this group is configured"""
        return group.get_robot_id(self._conx, group=self._id)

    @property
    def robot_model(self) -> str:
        """Returns the robot model for which this group is configured"""
        return group.get_robot_model(self._conx, group=self._id)

    @property
    def was_jogged(self) -> bool:
        """Whether or not this group was jogged since the last programmed
        motion
        """
        return group.was_jogged(self._conx, group=self._id)

    @property
    def active_jogframe(self) -> int:
        """The index of the currently active jogframe for this group"""
        return frames.get_active_jogframe(self._conx, group=self._id)

    @property
    def active_toolframe(self) -> int:
        """The index of the currently active toolframe for this group"""
        return frames.get_active_toolframe(self._conx, group=self._id)

    @property
    def active_userframe(self) -> int:
        """The index of the currently active userframe for this group"""
        return frames.get_active_userframe(self._conx, group=self._id)

    def payload(self, idx: int):
        """Returns the payload schedule at index 'idx' for this group"""
        return group.get_payload(self._conx, idx=idx, grp=self._id)

    def toolframe(self, idx: int) -> ToolFrame:
        """Returns the toolframe at index 'idx' for this group"""
        return ToolFrame(self._conx, idx, group=self._id)

    def userframe(self, idx: int) -> UserFrame:
        """Returns the userframe at index 'idx' for this group"""
        return UserFrame(self._conx, idx, group=self._id)

    def jogframe(self, idx: int) -> JogFrame:
        """Returns the jogframe at index 'idx' for this group"""
        return JogFrame(self._conx, idx, group=self._id)


class Variable(object):
    def __init__(self, conx: Connection, name: str, typ: Type):
        self._conx = conx
        self._name = name
        self._type = typ

    @property
    def name(self) -> str:
        return self._name

    @property
    def typ(self) -> Type:
        return self._type


class ScalarVariable(Variable):
    def __init__(
        self, conx: Connection, name: str, typ: Type[Union[bool, float, int, str]] = str
    ):
        if typ not in [bool, float, int, str]:
            raise UnsupportedVariableTypeException(
                "Only scalar variable types are supported (" f"got '{type(typ)}')"
            )
        super().__init__(conx, name, typ=typ)

    @property
    def val(self):
        return self.typ(variables.get_scalar_var(self._conx, name=self._name))

    @val.setter
    def val(self, val):
        if type(val) != self.typ:
            raise ValueError(f"Cannot write {type(val)} to variable of type {self.typ}")
        # we explicitly convert to str here, as set_scalar_var(..) will always
        # send values as strings
        variables.set_scalar_var(self._conx, name=self._name, val=str(val))


# TODO: fix this mess. This is not a nice way to wrap IO access
class IoElement(object):
    def __init__(self, conx: Connection, idx: int, port_type: str, port_type_w: str):
        self._conx = conx
        self._idx = idx
        self._port_type = port_type
        self._port_type_w = port_type_w

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def port_type(self) -> str:
        return self._port_type

    @property
    def port_type_w(self) -> str:
        return self._port_type_w


class BooleanIoElement(IoElement):
    def __init__(
        self,
        conx: Connection,
        idx: int,
        port_type: str,
        port_type_w: Optional[str] = None,
    ):
        assert port_type in [
            "BRAKE",
            "DIN",
            "DOUT",
            "ESTOP",
            "LDIN",
            "LDOUT",
            "PLCIN",
            "PLCOUT",
            "RDI",
            "RDO",
            "SOPIN",
            "SOPOUT",
            "TOOL",
            "TPIN",
            "TPOUT",
            "UOPIN",
            "UOPOUT",
            "WDI",
            "WDO",
            "WSIN",
            "WSOUT",
        ]
        if port_type_w:
            # KCL's 'set port' uses different port identifiers
            assert port_type_w in [
                "DIN",
                "DOUT",
                "RDO",
                "OPOUT",
                "TPOUT",
                "WDI",
                "WDO",
            ]
        else:
            port_type_w = port_type
        super().__init__(conx, idx, port_type, port_type_w)

    @property
    def val(self) -> bool:
        return io.io_read(self._conx, self._port_type, self._idx) == 'ON'

    @val.setter
    def val(self, val: bool) -> None:
        io.io_write(self._conx, self._port_type_w, self._idx, 1 if val else 0)


class IntegerIoElement(IoElement):
    def __init__(
        self,
        conx: Connection,
        idx: int,
        port_type: str,
        port_type_w: Optional[str] = None,
    ):
        assert port_type in [
            'ANIN',
            'ANOUT',
            'GPIN',
            'GPOUT',
            'LANIN',
            'LANOUT',
        ]
        if port_type_w:
            # KCL's 'set port' uses different port identifiers
            assert port_type_w in ['AIN', 'AOUT', 'GIN', 'GOUT']
        else:
            port_type_w = port_type
        super().__init__(conx, idx, port_type, port_type_w)

    @property
    def val(self) -> int:
        return io.io_read(self._conx, self._port_type, self._idx)

    @val.setter
    def val(self, val: int) -> None:
        io.io_write(self._conx, self._port_type_w, self._idx, val)


class Controller(object):
    def __init__(self, conx):
        self._conx = conx

    def numreg(self, idx: int) -> NumReg:
        return NumReg(self._conx, idx)

    def strreg(self, idx: int) -> StrReg:
        return StrReg(self._conx, idx)

    def posreg(self, idx: int) -> PosReg:
        return PosReg(self._conx, idx)

    def group(self, idx: int) -> MotionGroup:
        return MotionGroup(self._conx, idx)

    def variable(self, name: str, typ: Type = str) -> ScalarVariable:
        return ScalarVariable(self._conx, name, typ)

    def din(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'DIN')

    def dout(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'DOUT')

    def gin(self, idx: int) -> IoElement:
        return IntegerIoElement(self._conx, idx, 'GPIN', 'GIN')

    def gout(self, idx: int) -> IoElement:
        return IntegerIoElement(self._conx, idx, 'GPOUT', 'GOUT')

    def rdi(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'RDI')

    def rdo(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'RDO')

    def sopin(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'SOPIN')

    def sopout(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'SOPOUT', 'OPOUT')

    def uopin(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'UOPIN')

    def uopout(self, idx: int) -> IoElement:
        return BooleanIoElement(self._conx, idx, 'UOPOUT')

    def reset(self) -> None:
        """Attempts to RESET the controller"""
        controller.reset(self._conx)

    @property
    def series(self) -> str:
        return controller.get_controller_series(self._conx)

    @property
    def application(self) -> str:
        return controller.get_application(self._conx)

    @property
    def system_software_version(self) -> str:
        return controller.get_system_software_version(self._conx)

    @property
    def active_program(self) -> str:
        """Returns the name of the program currently being executed"""
        return controller.get_active_prog(self._conx)

    @property
    def num_groups(self) -> int:
        """Returns the number of motion groups configured on the controller"""
        return controller.get_num_groups(self._conx)

    @property
    def current_time(self) -> datetime.datetime:
        """Returns the current (wallclock) time on the controller

        Note: resolution is in minutes
        """
        return controller.get_clock(self._conx)

    @property
    def curr_line(self) -> int:
        return controller.get_curr_line(self._conx)

    @property
    def curr_routine(self) -> str:
        return controller.get_curr_routine(self._conx)

    @property
    def general_override(self) -> int:
        return controller.get_general_override(self._conx)

    @general_override.setter
    def general_override(self, val: int) -> None:
        controller.set_general_override(self._conx, val)

    @property
    def in_auto_mode(self) -> bool:
        return controller.in_auto_mode(self._conx)

    @property
    def tp_enabled(self) -> bool:
        return controller.tp_enabled(self._conx)

    @property
    def in_remote_mode(self) -> bool:
        return controller.in_remote_mode(self._conx)

    @property
    def is_e_stopped(self) -> bool:
        return controller.is_e_stopped(self._conx)

    @property
    def is_faulted(self) -> bool:
        return controller.is_faulted(self._conx)

    @property
    def is_program_paused(self) -> bool:
        return controller.is_program_paused(self._conx)

    @property
    def is_program_running(self) -> bool:
        return controller.is_program_running(self._conx)

    def list_errors(self) -> List[Tuple[int, str, str, str, str, str]]:
        return controller.list_errors(self._conx)

    def list_programs(self, types: List[str] = []):
        return controller.list_programs(self._conx, types)


def connect(
    host: str,
    helper_dev: str = 'td:',
    helper_dir: str = '',
    skip_helper_upload: bool = False,
    request_timeout: float = 5,
    kcl_auth: Optional[Tuple[str, str]] = None,
    karel_auth: Optional[Tuple[str, str]] = None,
    ftp_auth: Optional[Tuple[str, str]] = None,
) -> Controller:
    """Connect to the controller at 'host' and initialise a connection.

    Note: use 'skip_helper_upload' to override the default behaviour which
    always uploads the helpers. If they have already been uploaded (for
    instance by a previous or concurrent session), avoiding the upload could
    save some seconds during initialisation of this session.

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

    # TODO: do this some other way
    base_path = f'{helper_dev}/{helper_dir}'
    while '//' in base_path:
        base_path = base_path.replace('//', '/')
    if base_path.endswith('/'):
        base_path = base_path[:-1]

    helpers_uploaded = False
    if not skip_helper_upload:
        upload_helpers(host, base_path)
        helpers_uploaded = True

    conx = Connection(
        host,
        base_path,
        helpers_uploaded,
        skipped_helpers_upload=skip_helper_upload,
        request_timeout=request_timeout,
        kcl_auth=kcl_auth,
        karel_auth=karel_auth,
        ftp_auth=ftp_auth,
    )

    return Controller(conx)
