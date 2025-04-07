# check_rpm_last_update

This is a nagios plugin to check how long it has been since rpm packages were installed.
based on https://github.com/aptivate/check_yum_last_update/

Usage: check_rpm_last_update [options]

Options:

    -h, --help            show this help message and exit
    -w WARNING, --warning=WARNING
                          Issue WARNING if the last update was more than this
                          many days ago.
    -c CRITICAL, --critical=CRITICAL
                          Issue CRITICAL if the last update was more than this
                          many days ago.
    -t TIMEOUT, --timeout=TIMEOUT
                          Sets a timeout in seconds after which the plugin will
                          exit (defaults to 30 seconds).
    -v, --verbose         Verbose mode. Can be used multiple times to increase
                          output. Use -vvv for debugging output. By default only
                          one result line is printed as per Nagios standards
    -V, --version         Print version number and exit

