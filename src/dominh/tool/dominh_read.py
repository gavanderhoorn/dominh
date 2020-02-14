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
usage: dominh read [options] <host> <port_type> <index>

options:
  -h --help     Show this screen.
  --status      Change program exit status according to IO value:
                 OFF : exit status 0
                 ON  : exit status 1
                Note: this is only supported for port types that
                map to boolean values.

"""

import sys

from docopt import docopt
from requests import exceptions

from dominh import Client, DominhException


def main(argv, skip_upload=False):
    args = docopt(__doc__, argv=argv)

    port_type = args['<port_type>']
    index = int(args['<index>'])
    status = args['--status']

    try:
        c = Client(args['<host>'], skip_helper_upload=skip_upload)
        c.initialise()

        val = c.io_read(port_type, index)
        valp = 1 if val == 'ON' else 0
        if status:
            sys.exit(valp)
        print (valp)

    except (exceptions.ConnectionError, OSError) as e:
        sys.stderr.write("Error trying to connect to the controller: {}\n".format(e))
    except DominhException as e:
        sys.stderr.write("Error during read: {}\n".format(e))
