#!/usr/bin/env python2
"""gmxmail

Usage:
    gmxmail (get|send <recipient> <head> <message> [[-s] [-e] [-k]])
            [-a <acc>] [-u <user>] [-q] [-h] [-v...]

Arguments:
    get                Get mail (for the default account, unless -a).
    send               Send a mail. Recipients comma-separated, message quoted.
                       Head is cc::bcc::subject, cc::::subject or just subject.
                       Optionally, you can sign/encrypt the message or attack
                       your public key. All three with -sek.

Options:
    -a, --acc=<acc>    Account to send the e-mail from.
    -u, --user=<user>  Username to use as login, if necessary. Defaults to acc.
    -s, --sign         Sign the mail with your GPG Key.
    -e, --encrypt      Encrypt the mail.
    -k, --key          Attach your public key to the mail.
    -h, --help         Show this help message and exit.
    -q, --quiet        Do not log bot events to stdout. Will still log to file.
    -v                 Logging verbosity, up to -vvv.
"""

import logging
import os
import sys

from docopt import docopt

from mail import MailHandler


log = logging.getLogger("main")


def init_logging(quiet, loglevel, configdir):
    "Initializes the console and file handlers for the logging module."
    logger = logging.getLogger()

    # Set the loglevel.
    if loglevel > 3:
        loglevel = 3
    loglevel = 3
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[loglevel])

    logformat = "%(asctime)-14s %(levelname)-7s %(name)-5s %(message)s"

    formatter = logging.Formatter(logformat)

    try:
        logfile = os.path.join(configdir, "gmxmail.log")
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        log.info("Added logging file handler.")
    except IOError:
        log.info("Could not attach file handler.")

    # By default, we log to both file and stdout, unless quiet is enabled.
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log.info("Added logging console handler.")


def get_configdir():
    "Determines where to store our logs and read our config file from."
    configdir = os.path.dirname(os.path.realpath(__file__))  # We are here.
    home = os.path.join(os.path.expanduser("~"), ".gmxmail")
    homeconfig = os.path.join(os.path.expanduser("~"), ".config/gmxmail")
    if os.path.isdir(homeconfig):
        configdir = homeconfig
    elif os.path.isdir(home):
        configdir = home

    return configdir


def main():
    "Entry point for gmxmail."
    args = docopt(__doc__, version="0.1")
    print args
    configdir = get_configdir()

    init_logging(args["--quiet"], args["-v"], configdir)

    m = MailHandler(args["--acc"], args["--user"], configdir)

    if args["send"]:
        m.send_mail(args["<recipient>"], args["<head>"], args["<message>"],
                    args["--sign"], args["--encrypt"], args["--key"])
    else:
        m.get_mail()

if __name__ == "__main__":
    main()