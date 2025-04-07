#!/usr/bin/env python3

# plugin to check how long since the last update was done
# shamelessly based on https://github.com/aptivate/check_yum_last_update/

__author__ = "Georg Schlagholz/IT-Native"
__title__ = (
    "Nagios Plugin for checking days since last RPM update on RedHat/CentOS systems"
)
__version__ = "0.0.1"


import os
import signal
import subprocess
import sys
from datetime import datetime
from optparse import OptionParser

# Standard Nagios return codes
OK       = 0
WARNING  = 1
CRITICAL = 2
UNKNOWN  = 3

DEFAULT_TIMEOUT = 30
DEFAULT_WARNING = 60
DEFAULT_CRITICAL = 90

RPM = "/usr/bin/rpm"


def end(status, message):
    """Exits the plugin with first arg as the return code and the second
    arg as the message to output"""

    if status == OK:
        print("OK: %s" % message)
        sys.exit(OK)
    elif status == WARNING:
        print("WARNING: %s" % message)
        sys.exit(WARNING)
    elif status == CRITICAL:
        print("CRITICAL: %s" % message)
        sys.exit(CRITICAL)
    else:
        print("UNKNOWN: %s" % message)
        sys.exit(UNKNOWN)


def check_rpm_usable():
    """Checks that the RPM program and path are correct and usable - that
    the program exists and is executable, otherwise exits with error"""

    if not os.path.exists(RPM):
        end(UNKNOWN, "%s cannot be found" % RPM)
    elif not os.path.isfile(RPM):
        end(UNKNOWN, "%s is not a file" % RPM)
    elif not os.access(RPM, os.X_OK):
        end(UNKNOWN, "%s is not executable" % RPM)


class RPMUpdateChecker(object):
    def __init__(self):
        """Initialize all object variables"""

        self.timeout = DEFAULT_TIMEOUT
        self.verbosity = 0

    def validate_all_variables(self):
        """Validates all object variables to make sure the
        environment is sane"""

        if self.timeout is None:
            self.timeout = DEFAULT_TIMEOUT
        try:
            self.timeout = int(self.timeout)
        except ValueError:
            end(
                UNKNOWN,
                "Timeout must be an whole number, "
                + "representing the timeout in seconds",
            )

        if self.timeout < 1 or self.timeout > 3600:
            end(UNKNOWN, "Timeout must be a number between 1 and 3600 seconds")

        if self.warning is None:
            self.warning = DEFAULT_WARNING
        try:
            self.warning = int(self.warning)
        except ValueError:
            end(
                UNKNOWN,
                "Warning must be an whole number, "
                + "representing the update time limit in days",
            )
        if self.warning < 1 or self.warning > 3650:
            end(UNKNOWN, "Warning must be a number between 1 and 3650 days")

        if self.critical is None:
            self.critical = DEFAULT_CRITICAL
        try:
            self.critical = int(self.critical)
        except ValueError:
            end(
                UNKNOWN,
                "Critical must be an whole number, "
                + "representing the update time limit in days",
            )
        if self.critical < 1 or self.critical > 3650:
            end(UNKNOWN, "Critical must be a number between 1 and 3650 days")

        if self.warning > self.critical:
            end(UNKNOWN, "Warning cannot be larger than critical")

        if self.verbosity is None:
            self.verbosity = 0
        try:
            self.verbosity = int(self.verbosity)
            if self.verbosity < 0:
                raise ValueError
        except ValueError:
            end(
                UNKNOWN, "Invalid verbosity type, must be positive numeric " + "integer"
            )

    def set_timeout(self):
        """sets an alarm to time out the test"""

        if self.timeout == 1:
            self.vprint(3, "setting plugin timeout to %s second" % self.timeout)
        else:
            self.vprint(3, "setting plugin timeout to %s seconds" % self.timeout)

        signal.signal(signal.SIGALRM, self.sighandler)
        signal.alarm(self.timeout)

    def sighandler(self, discarded, discarded2):
        """Function to be called by signal.alarm to kill the plugin"""

        # Nop for these variables
        discarded = discarded2
        discarded2 = discarded

        end(
            CRITICAL,
            "RPM nagios plugin has self terminated after "
            + "exceeding the timeout (%s seconds)" % self.timeout,
        )

    def vprint(self, threshold, message):
        """Prints a message if the first arg is numerically greater than the
        verbosity level"""
        if self.verbosity >= threshold:
            print("%s" % message)

    def calc_days_ago(self, date):
        datediff = date.today() - date
        return datediff.days

    def check_last_rpm_update(self):
        check_rpm_usable()
        self.validate_all_variables()
        self.vprint(
            3, "%s - Version %s\nAuthor: %s\n" % (__title__, __version__, __author__)
        )

        self.set_timeout()
        result = subprocess.run(
            [RPM, "-qa", "--last"], stdout=subprocess.PIPE, check=True
        )
        last_update = " ".join(result.stdout.decode().splitlines()[0].split()[1:])
        last_update = datetime.strptime(last_update, "%a %d %b %Y %I:%M:%S %p %Z")

        if last_update is None:
            # RPM never run
            status = CRITICAL
            message = "No date in RPM history found, it probably never ran"
        else:
            days_since_update = self.calc_days_ago(last_update)
            if days_since_update == 1:
                message = "1 day since last rpm update"
            else:
                message = "%d days since last rpm update" % days_since_update

            if days_since_update < self.warning:
                status = OK
            elif days_since_update < self.critical:
                status = WARNING
            else:
                status = CRITICAL
        return status, message


def main():
    """Parses command line options and calls the test function"""

    update_checker = RPMUpdateChecker()
    parser = OptionParser()

    parser.add_option(
        "-w",
        "--warning",
        dest="warning",
        help="Issue WARNING if the last update was more than " + "this many days ago.",
    )

    parser.add_option(
        "-c",
        "--critical",
        dest="critical",
        help="Issue CRITICAL if the last update was more than " + "this many days ago.",
    )

    parser.add_option(
        "-t",
        "--timeout",
        dest="timeout",
        help="Sets a timeout in seconds after which the "
        + "plugin will exit (defaults to %s seconds). " % DEFAULT_TIMEOUT,
    )

    parser.add_option(
        "-v",
        "--verbose",
        action="count",
        dest="verbosity",
        help="Verbose mode. Can be used multiple times to "
        + "increase output. Use -vvv for debugging output. "
        + "By default only one result line is printed as "
        + "per Nagios standards",
    )

    parser.add_option(
        "-V",
        "--version",
        action="store_true",
        dest="version",
        help="Print version number and exit",
    )

    (options, args) = parser.parse_args()

    if args:
        parser.print_help()
        sys.exit(UNKNOWN)

    update_checker.warning = options.warning
    update_checker.critical = options.critical
    update_checker.timeout = options.timeout
    update_checker.verbosity = options.verbosity

    if options.version:
        print("%s - Version %s\nAuthor: %s\n" % (__title__, __version__, __author__))
        sys.exit(OK)

    result, output = update_checker.check_last_rpm_update()
    end(result, output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Caught Control-C...")
        sys.exit(CRITICAL)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
