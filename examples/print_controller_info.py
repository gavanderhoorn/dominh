#!/usr/bin/env python3

# flake8: noqa

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
Usage: print_controller_info.py [(--user=<user> --pw=<pw>)] <host>

"""

from docopt import docopt

import dominh


if __name__ == '__main__':
    args = docopt(__doc__, version=f'dominh {dominh.__version__}')
    host = args['<host>']
    user = args['--user']
    pw = args['--pw']

    print(f'Attempting to connect to: {host}')

    auth = None
    if user:
        print("Assuming KCL and Karel resources share credentials.")
        auth = (user, pw)
    c = dominh.connect(host, kcl_auth=auth, karel_auth=auth)

    print('\nController info:')
    print(f'  Time                  : {c.current_time}')
    print(f'  Series                : {c.series}')
    print(f'  Application           : {c.application}')
    print(f'  Software version      : {c.system_software_version}')
    print(f'  $FNO                  : {c.variable("[*system*]$fno", typ=str).val}')

    print('\nRobot info:')

    num_groups = c.num_groups
    print(f'  Number of groups      : {num_groups}')

    for grp in [c.group(i + 1) for i in range(num_groups)]:
        print(f'  Group {grp.id}:')
        print(f'    ID                  : {grp.robot_id}')
        print(f'    Model               : {grp.robot_model}')
        print(f'    Current pose        : {grp.curpos}')

    print(f'\nGeneral override        : {c.general_override}%')

    print('\nController status:')
    print(f'  TP enabled            : {c.tp_enabled}')
    print(f'  In AUTO               : {c.in_auto_mode}')
    print(f'  In error              : {c.is_faulted}')
    print(f'  E-stopped             : {c.is_e_stopped}')
    print(f'  Remote mode           : {c.in_remote_mode}')
    print(f'  Program running       : {c.is_program_running}')
    print(f'  Program paused        : {c.is_program_paused}')

    numregs = ', '.join([str(c.numreg(i + 1).val) for i in range(5)])
    print(f'\nFirst 5 numregs         : {numregs}')

    sopins = ', '.join([str(c.sopin(i + 1).val) for i in range(5)])
    print(f'\nFirst 5 SOP inputs      : {sopins}')

    pld = c.group(1).payload(1)
    pld_frame = f'({pld.payload_x}, {pld.payload_y}, {pld.payload_z})'
    pld_inertia = f'{pld.payload_ix}, {pld.payload_iy}, {pld.payload_iz}'
    print(
        f'\nPayload 1 in group 1    : {pld.payload} Kg at {pld_frame} (inertia: {pld_inertia})'
    )

    prgs = '; '.join([f"{nam}.{ext}" for nam, ext in c.list_programs()[:5]])
    print(f'\nFirst five programs     : {prgs}')

    errs = '\n  '.join(
        [
            f'{stamp} {lvl:7s} {msg}'
            for _, stamp, msg, _, lvl, _ in c.list_errors()[:5]
        ]
    )
    print(f'\nFive most recent errors:\n  {errs}')
