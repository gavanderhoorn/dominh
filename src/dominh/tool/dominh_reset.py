#!/usr/bin/env python3

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


"""
usage: dominh reset [options] <host>

options:
  -h --help     Show this screen.
  --verify      Verify controller was successfully reset. Exit status
                reflects success of operation.

"""

import sys

from docopt import docopt
from requests import exceptions

from dominh import Client


def main(argv):
    args = docopt(__doc__, argv=argv)

    # we don't need helpers to be able to reset the controller, so skip
    # uploading them, unless user wants to verify fault status, then we do
    # need them (they're used to read IOs)
    need_helpers = args['--verify']

    try:
        c = Client(args['<host>'], skip_helper_upload=not need_helpers)
        c.initialise()
        c.reset()

        if (args['--verify']):
            sys.exit(1 if c.is_faulted() else 0)
        sys.exit(0)
    except exceptions.ConnectionError as e:
        sys.stderr.write(
            "Error trying to connect to the controller: {}\n".format(e))
