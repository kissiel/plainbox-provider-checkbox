#!/usr/bin/env python3
import re
import subprocess
import sys
import time

from pprint import pprint as print


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
    entry['speed'] = match.group(1) if match else "Unknown"
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

    def wait_for_new(self, timeout=30):
        while timeout >= 0:
            new = self.whats_new()
            if new:
                return new
            time.sleep(1)
            timeout -= 1
        return []

    def wait_for_removal(self, timeout=30):
        while timeout >= 0:
            new = self.whats_new()
            if not new:
                return True
            time.sleep(1)
            timeout -= 1
        return False

def main():
    pass


if __name__ == '__main__':
    main()
