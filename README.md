# Dominh

[![license - apache 2.0](https://img.shields.io/:license-Apache%202.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/gavanderhoorn/dominh/workflows/CI/badge.svg?branch=master)](https://github.com/gavanderhoorn/dominh/actions?query=workflow%3ACI)
[![Github Issues](https://img.shields.io/github/issues/gavanderhoorn/dominh.svg)](https://github.com/gavanderhoorn/dominh/issues)

## Overview

This is a poor man's version of a subset of the RPC functionality provided by the (Windows-only) Fanuc PCDK implemented in Python.
This uses the *Web Svr Enhancements* option (`R626`) and the interfaces it provides to the controller (see note in [Requirements](#requirements)).
Only a subset of the functionality is currently available and performance will not be comparable with the PCDK.

Additionally a simple set of CLI tools is included, which allows some of the library's functionality to be used from the command line and/or in shell scripts.

**NOTE**: this is only meant as an example of such a remote control facility.
Proper integration of a Fanuc controller with an external application or workcell should be done using either the real PCDK, a fieldbus or similar technology.
The scripts and functionality provided here are only a convenience and are only intended to be used in academic and laboratory settings.
They allow incidental external access to a controller without needing to use any additional hardware.
Do not use this on production systems or in contexts where any kind of determinism is required.
The author recommends using PCDK and/or any of the supported fieldbuses in those cases.

**NOTE 2**: on R-30iB+ controllers, option `R912` can do some of the things this library supports.

## TOC

1. [Requirements](#requirements)
1. [Compatibility](#compatibility)
1. [Installation](#installation)
1. [Example usage](#example-usage)
1. [Supported functionality](#supported-functionality)
1. [Limitations / Known issues](#limitations-known-issues)
1. [Performance](#performance)
1. [Related projects](#related-projects)
1. [Bugs, feature requests, etc](#bugs-feature-requests-etc)
1. [FAQ](#faq)
1. [Disclaimer](#disclaimer)

## Requirements

This needs the base *Web Server* (`HTTP`) and the *Web Svr Enhancements* (`R626`) options (note: contrary to what the manual states, this is not a separate option: all functionality is already built-in, at least for R-30iA and newer controllers).
As some parts are written in Karel, option `R632` could be a requirement, but this is unlikely.

Other requirements include a functioning networking setup (make sure you can ping the controller and the controller's website shows up when opening `http://robot_ip`), and correctly configured *HTTP Authentication* and FTP server settings.
Either unlock the *KAREL* and *KCL* resources completely or configure sets of credentials for both resources.
Configuration for the built-in FTP server should be OK by default, but may be changed to also require a username and password.
Refer to section 6.5 *HTTP AUTHENTICATION* of the *FANUC Robot series - Ethernet Function - Operator's Manual* (document `B-82974EN` for the R-30iA) for more information.

## Compatibility

### Controllers

Compatibility has only been tested with R-30iA and R-30iB+ controllers running V7.70, V9.10 and V9.30 of the system software, but others are expected to be compatible as well, as long as they have the required options (or equivalents).

### Operating Systems

The library and CLI tools have been written for Python version 3.
No specific OS dependencies are known, so all platforms with a Python 3 interpreter should be supported.
Only Ubuntu Xenial, Bionic and Focal have been extensively tested however.

## Installation

### Helpers

Translate all `.kl` files in `res/kl` either with Roboguide or with the supplied `Makefile`.
The latter will require a compatible version of GNU Make for Windows to be available on the `%PATH%`.
Now copy the resultant `.pc` files to the controller.

Finally, make sure to check the web server security settings (see [Requirements](#requirements)).

No further setup is required.

### Package

It's recommended to use a virtual Python 3 environment and install the package in it.
Due to the heavy use of f-strings, at least Python 3.6 is required.
The author has primarily used Python 3.8, but other versions are expected to work.

Future versions may be released to PyPi.

Example (install dominh `0.3.0`; be sure to update the URL to download the desired version):

```shell
python3 -m venv $HOME/venv_dominh
source $HOME/venv_dominh/bin/activate
pip install -U pip wheel setuptools
pip install https://github.com/gavanderhoorn/dominh/archive/0.3.0.tar.gz
dominh --version
```

The last command should then print "`dominh 0.3.0`".

## Example usage

### Example script

The `examples` directory contains an example script which uses some of the functionality of `dominh` to print various bits of information retrieved from a controller.

Example output for an R-30iA with an M-10iA in Roboguide:

<details><summary>Click to expand</summary>

```console
$ python examples/print_controller_info.py localhost
Attempting to connect to: localhost

Controller info:
  Time                  : 2020-11-23 10:19:00
  Series                : R-30iA
  Application           : HandlingTool
  Software version      : V7.70P/48
  $FNO                  : 12345

Robot info:
  Number of groups      : 1
  Group 1:
    ID                  : M-10iA
    Model               : M-10iA

General override        : 100%

Controller status:
  TP enabled            : False
  In AUTO               : True
  In error              : False
  E-stopped             : False
  Remote mode           : False
  Program running       : False
  Program paused        : False

First 5 numregs         : 1.234, 0, 0, 0, 0

First 5 SOP inputs      : False, True, True, False, False

Payload 1 in group 1    : 10.0 Kg at (0.0, 0.0, 0.0) (inertia: 0.0, 0.0, 0.0)

First five programs     : -BCKED8-.TP; -BCKED9-.TP; -BCKEDT-.TP; ATERRJOB.VR; GEMDATA.PC

Five most recent errors:
  23-NOV-20 10:18         R E S E T
  23-NOV-20 09:47         R E S E T
  23-NOV-20 09:47 WARN    SRVO-012 Power failure recovery
  23-NOV-20 09:47 WARN    INTP-127 Power fail detected
  23-NOV-20 09:47         R E S E T
```

</details>

Note: this script *may* fail on controllers which do not have `UOP` and `SOP` configured ([gavanderhoorn/dominh#7](https://github.com/gavanderhoorn/dominh/issues/7)).

### Library

The following shows a short example of how this library could be used to connect to a controller with credentials for access to the `KAREL` resource, reset the controller, then set the override to 100% and finally read the `DOUT[1]` IO element.

<details><summary>Click to expand</summary>

```python
from dominh import connect

# replace '<robot_ip>' with the IP of the controller
c = connect('<robot_ip>', karel_auth=('user', 'pass'))

c.reset()
# Karel RefMan suggests waiting for 1 second
time.sleep(1.0)

if (c.is_faulted):
    print ("Still faulted")
else:
    print ("All green")

c.general_override = 100

dout1_state = c.dout(1).val

...
```

</details>

### CLI

<details><summary>Click to expand</summary>

```bash
# replace '<robot_ip>' with the IP of the controller
export ROBOT_IP=<robot_ip>

# reset a controller (fire-and-forget)
dominh reset $ROBOT_IP

# reset the controller and indicate success using the exit code of
# the program
dominh reset --verify $ROBOT_IP
echo $?

# retrieve the value of the $FNO system variable.
#
# note the single quotes around the name, to prevent the shell from
# interpreting it as an env variable
dominh get $ROBOT_IP '$fno'

# read the state of DOUT[1]
dominh read $ROBOT_IP DOUT 1

# turn off DOUT[1]
dominh write $ROBOT_IP DOUT 1 0

# check whether controller is faulted (SO[3] = Fault LED)
dominh read $ROBOT_IP SOPOUT 3
```

</details>

## Supported functionality

Dominh can currently be used to (incomplete list):

* fault reset the controller
* determine whether the controller is:
  * faulted
  * e-stopped
  * executing a program
  * paused
  * in AUTO or MANUAL mode
  * in REMOTE mode
* determine whether the TP is enabled
* determine the controller series (ie: R-30iA, R-30iB, R-30iB+)
* retrieve the application software (ie: HandlingTool, etc)
* retrieve the version of the application software
* retrieve the controller's time and date
* read/write (system) variables (scalar variables are mostly supported)
* read/write IO elements (digital, analogue, group, UOP, SOP, TP, flags, markers, etc)
* read/write numerical registers
* read/write string registers
* retrieve the number of numerical and string registers
* read/write the general override
* retrieve the number of defined groups
* retrieve the ID and model of configured robots
* retrieve jog, tool and user frames
* retrieve currently active jog, tool or user frame
* retrieve payload schedules
* retrieve the list of errors (including history)
* retrieve a list of programs (filtered by program type)
* update the comments of numeric, string and position registers and digital IO in and out elements

The above list only includes the functionality offered by the `Controller` class' public interface and that of the returned objects.
Much more is possible (especially in the area of system variable wrapping/retrieving), but would require adding more convenience methods.

## Limitations / Known issues

The following limitations and known issues exist:

* Only a small subset of the functionality offered by the PCDK is supported.
* Several methods have a high runtime overhead.
  This is largely caused by the use of the Fanuc web server as an intermediary and the resulting need to download and parse returned HTML.
  The library makes use of `.stm` files and zero-output KCL commands where possible, but cannot avoid parsing some pages.
* Not all methods are symmetric (ie: not all getters have setters).
  This may change in the future.
* "Robot Out" (ie: `RDO`) is not writable. The port name as specified in the Fanuc manual on KCL does not seem to work.
* Dominh CLI tools wrap only a subset of the library's functionality.
* CLI tools currently do not support authentication
* Even though some helpers return JSON, HTTP headers returned by the web server do not reflect this.
  This is a limitation of the web server used by Fanuc.
* HTTP status return codes do not reflect the result of operations in all cases.
  This is again a limitation of the web server used by Fanuc.

## Performance

As an indication of the performance: reading `DOUT[1]` from an idle R-30iB+ takes about 300 to 400 ms.
Retrieving the value of the `$FNO` system variable from the same controller takes also about 300 to 400 ms.

In both cases the helpers were already present on the controller and the controller was idle (ie: no user TP or Karel programs were running).

## Related projects

For a similar library, but written in Go, see [onerobotics/go-fanuc](https://github.com/onerobotics/go-fanuc).

## Bugs, feature requests, etc

Please use the [GitHub issue tracker](https://github.com/gavanderhoorn/dominh/issues).

## FAQ

### Doesn't this emulate the PCDK?

Yes, it does.

### Why create it then?

The PCDK is primarily targeted at Windows and .NET and C++.
I needed something that worked on a non-Windows OS and with languages other than .NET and C++.
Python was a natural choice for me.

### Why did you not use Go/Rust/Java/Kotlin/Swift/anything but Python?

Time and application requirements: target framework supported Python, so writing Dominh in Python made sense.

### This is far from production-ready code

Yes, I agree.
See also the *NOTE* in the *Overview* section.

### Performance is really bad

Compared to the PCDK: certainly, but if you need a more performant solution, ask Fanuc for a PCDK license or use a fieldbus.
If you have ideas on how to improve performance, post an issue [on the tracker](https://github.com/gavanderhoorn/dominh/issues).

### Why not use Karel more?

While it would certainly possible to delegate much more of the functionality to Karel programs on the controller, it would also increase the 'footprint' of dominh.
As much of the functionality is not intended to be used in performance critical parts of applications, I decided it would be interesting to see how much could be done with existing interfaces and functionality already provided by Fanuc.
Dominh uses the KCL and built-in web server as much as possible.
Only where absolutely necessary (or where very much more efficient) is Karel used.

### Can I submit feature/enhancement requests?

Of course!
I can't guarantee I'll have time to work on them though.

### Would you take pull requests which add new features?

Most certainly.
As long as new features (or enhancements of existing functionality) pass CI and are reasonably implemented, they will be merged.

### How should Dominh be pronounced?

Domin-a (the `h` is silent).

## Disclaimer

The author of this software is not affiliated with FANUC Corporation in any way.
All trademarks and registered trademarks are property of their respective owners, and company, product and service names mentioned in this readme or appearing in source code or other artefacts in this repository are used for identification purposes only.
Use of these names does not imply endorsement by FANUC Corporation.
