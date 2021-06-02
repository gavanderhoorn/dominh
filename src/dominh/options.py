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


import typing as t

from .connection import Connection
from .helpers import get_file_as_bytes


def get_features(conx: Connection) -> t.List[t.Tuple[str, str]]:
    """Retrieve the list of options installed on the controller.

    Note: demo options are not included.

    :returns: list of options installed on the controller
    :rtype: list(tuple(str, str))
    """
    version_dg = get_file_as_bytes(conx, '/md:/version.dg')
    res = []
    # Yes, could have used use a regex here. But this also works.
    in_feature_section = False
    for line in version_dg.decode('ascii').splitlines():
        if not in_feature_section and line.lower().startswith("feature"):
            in_feature_section = True
            continue
        if in_feature_section and line == '':
            in_feature_section = False
            break
        if in_feature_section:
            # lines are of the form: <desc_sometimes_with_spaces> <order_nr>
            desc, _, option_no = line.strip().rpartition(' ')
            res.append((option_no, desc))
    return res


def has_feature(
    conx: Connection, option_no: str, features: t.List[t.Tuple[str, str]] = []
) -> bool:
    """Check whether a specific option is installed on the controller.

    Note: demo options are not checked.

    :param option_no: The option to check for
    :type option_no: str
    :param features: If supplied, check the given list instead of the controller
    :type features: list(tuple(str, str))
    :returns: True IFF 'option_no' is present
    :rtype: bool
    """
    features = features or get_features(conx)
    return option_no.upper() in dict(features)
