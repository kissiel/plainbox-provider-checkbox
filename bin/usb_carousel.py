#!/usr/bin/env python3
"""
This program guides the operator in testing all of the USB ports on the system.
"""

import re
import select
import subprocess
import sys
import time

from collections import defaultdict
from functools import partial


def run_lsusb():
    """Run `lsusb -t` and return its output as a string."""
    try:
        return subprocess.check_output(
            ['lsusb', '-t']).decode(sys.stdout.encoding)
    except Exception as exc:
        raise SystemExit("Failed to run `lsusb`. {}".format(exc))


def trim_lsusb_line(line):
    """Remove leading characters from a line of lsusb's output."""
    match = re.search(r'.*(Port\ .*)', line)
    if match:
        return match.group(1)
    return None


def parse_lsusb_line(line):
    """Turn a line of lsusb's output into a record."""
    entry = dict()
    # the following sequence of re searchers could be made more efficient by
    # creating one regex to cover all groups. But because some fields are
    # optional I decided to trade efficiency for readability
    match = re.search(r'(?<=Port\ )[0-9]+', line)
    entry['port'] = match.group(0) if match else "Unknown"

    match = re.search(r'(?<=Dev\ )[0-9]+', line)
    entry['dev'] = match.group(0) if match else "Unknown"

    match = re.search(r'(?<=If\ )[0-9]+', line)
    entry['if'] = match.group(0) if match else "Unknown"

    match = re.search(r'(?<=Class=)[^,]+', line)
    entry['class'] = match.group(0) if match else "Unknown"

    match = re.search(r'(?<=Driver=)[^,]+', line)
    entry['driver'] = match.group(0) if match else "Unknown"

    match = re.search(r'.*, (.*)', line)
    speed = match.group(1) if match else "Unknown"
    entry['standard'] = {
        '1.5M': 'USB 1.0',
        '12M': 'USB 1.1',
        '480M': 'USB 2.0',
        '5000M': 'USB 3.0',
        '10000M': 'USB 3.1',
        '20000M': 'USB 3.2',
        '40000M': 'USB 4.0'
    }.get(speed, 'Unknown')
    return entry


class LsusbScraper:
    """Interface to lsusb command."""

    def __init__(self):
        self.baseline = [
            trim_lsusb_line(l) for l in run_lsusb().splitlines() if l]

    def whats_new(self):
        """Return all the USB devices since LsusbScraper got created."""
        new_scrape = [
            trim_lsusb_line(l) for l in run_lsusb().splitlines() if l]
        return [l for l in new_scrape if l not in self.baseline]

    def wait_for_new(self, timeout=30, sleep_fn=time.sleep):
        """
        Wait for `timeout` seconds or until a new USB device got picked up
        by the lsusb command.
        `sleep_fn` will be used for waiting. If that callable returns
        a value that casts to True then the internal wait loop is aborted.
        """
        while timeout >= 0:
            new = self.whats_new()
            if new:
                return new
            if sleep_fn(1):
                break
            timeout -= 1
        return []

    def wait_for_removal(self, timeout=30):
        """Wait for lsusb command to pickup device removal."""
        while timeout >= 0:
            new = self.whats_new()
            if not new:
                return True
            time.sleep(1)
            timeout -= 1
        return False


def wait_for_enter(timeout):
    """
    Wait for `timeout` seconds for enter to be pressed.
    Return True if enter was pressed, or False if timeout was reached
    """
    read, _, __ = select.select([sys.stdin], [], [], timeout)
    if read:
        # need to consume the buffer, so the line does not linger on
        sys.stdin.readline()
        return True
    return False



def main():
    fprint = partial(print, flush=True)
    """Entry point to the program."""
    fprint("Remove all USB devices from all USB ports.")
    fprint("Press enter when you're done or wait 60s.")
    wait_for_enter(60)
    insertions = []
    scraper = LsusbScraper()
    fprint("Insert the device into the first port (30s timeout).")
    insertion = scraper.wait_for_new()
    if not insertion:
        raise SystemExit("Insertion not detected. Failing the test!")
    fprint("Devce detected: {}".format(insertion))
    insertions.append(parse_lsusb_line(insertion[0]))
    fprint("Remove the device from the port. (30s timeout).")
    if not scraper.wait_for_removal():
        raise SystemExit("Removal not detected. Failing the test!")
    while True:
        fprint("Insert the device to the next port (30s timeout).")
        fprint("If all ports were tested then wait 30s or press enter.")
        insertion = scraper.wait_for_new(30, wait_for_enter)
        if not insertion:
            break
        insertions.append(parse_lsusb_line(insertion[0]))
        fprint("Devce detected: {}".format(insertion))
        fprint("Remove the device from the port. (30s timeout).")
        if not scraper.wait_for_removal():
            raise SystemExit("Removal not detected. Failing the test!")
    fprint("\nSUMMARY\n")
    fprint("Detected {} device insertion(s)".format(len(insertions)))
    port_stats = defaultdict(set)
    for i in insertions:
        port_stats[i['standard']].add(i['port'])
    for std in sorted(port_stats.keys()):
        fprint("Detected {} unique {} port(s)".format(
            len(port_stats[std]), std))


if __name__ == '__main__':
    main()
