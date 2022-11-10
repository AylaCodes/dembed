"""
Simple watchdog to monitor a folder and create discord-embeddable html files for images.

The script checks every provided poll_rate (Default 1 second) if a new image has been
detected, and if so, creates the html files from the provided jinja2 template using
replacement variables from `main.json`.

Usage:

    dembed.py <folder> [poll_rate]
"""

import time
import sys
import json

from typing import List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

class Dembed:
    """
    Image folder watchdog.

    Attributes:
        directory: Folder to watch for new images in.
        poll_rate: Frequency in seconds to check for new images.
        monitor: Whether or not the watchdog is currently running.
        file_list: A list of files currently known by the watchdog.
        extensions: A list of file extensions which will trigger the generator.
        template: The jinja2 template to use for generating html files.
    """
    def __init__(self, directory: Path, poll_rate: int = 1, vars: dict = {}):
        self._first_run: bool = True
        self._environment = Environment(loader=FileSystemLoader("templates"))
        self.directory: Path = directory
        self.poll_rate: int = int(poll_rate)
        self.vars: dict = vars
        self.monitor: bool = False
        self.file_list: list[Path] = []
        self.extensions = [".jpg", ".png", ".jpeg"]
        self.template = self._environment.get_template("main.jinja")

    def get_contents(self) -> List[Path]:
        """Returns a list of files from the `Dembed.directory`"""
        return [
            f for f in self.directory.iterdir() if f.suffix in self.extensions
        ]

    def generate_html(self, file: Path) -> None:
        """Generates html file for given `file` using `Dembed.template`"""
        with open(f"{file.with_suffix('')}.html", "w") as html:
            html.write(self.template.render(file_name=file.name, **self.vars))

    def run_monitor(self) -> None:
        """Starts the watchdog"""
        self.monitor = True

        while self.monitor:
            if self._first_run:
                self.file_list = self.get_contents()
                self.monitor = True
                self._first_run = False

            # Check for file changes by comparing a set of the last-known file list to
            # a set of the file list for this polling interval
            changes = set(self.file_list).symmetric_difference(set(self.get_contents()))
            if changes:
                for item in changes:
                    if item in self.file_list:
                        # File was deleted, remove it from list
                        self.file_list.remove(item)
                        continue

                    self.file_list.append(item)
                    self.generate_html(item)

            time.sleep(self.poll_rate)

    def stop_monitor(self) -> None:
        """Stops the watchdog"""
        self.monitor = False

def usage() -> None:
    """Prints command line usage"""
    print("Usage: dembed.py <folder> [poll_rate]")

def main() -> None:
    # This is far from elegant, however it suits my simple needs and purposes
    try:
        folder = sys.argv[1]
    except Exception as e:
        print(f"Error: {e}")
        usage()

    try:
        poll_rate = sys.argv[2]
    except:
        print("No or invalid poll_rate provided, setting poll rate to 1 second.")
        poll_rate = 1

    vars = json.loads(Path("./templates/main.json").read_text())

    watchdog = Dembed(Path(sys.argv[1]), sys.argv[2], vars)
    watchdog.run_monitor()

if __name__ == "__main__":
    main()
