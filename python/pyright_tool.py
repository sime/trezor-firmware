"""
Wrapper around pyright type checking to allow us for easy inline
ignore of specific error messages.

Usage:
- run pyright natively to see the generated error messages
- try the best to fix it
- if unsuccessful, put "# pyright: ignore [<some error substring>]"
    as a comment to the line we want to ignore
    - "# pyright: ignore [<error1>;;<error2>;;...]" if there are more than one errors on that line
- run this tool and see if that error is no longer reported

TODO FEATURES:
- error handling for all cases

ISSUES:
- "# pyright: ignore" is not understood by `black` as a type comment, so it is being affected
    and restyled - we might have to use "# type: ignore" instead
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

Error = Dict[str, Any]
Errors = List[Error]


@dataclass
class IgnoreStatement:
    substring: str
    already_used: bool = False

    def __setitem__(self, key: str, value: Any) -> None:
        self.key = value


@dataclass
class LineIgnore:
    line_no: int
    ignore_statements: List[IgnoreStatement]

    def __setitem__(self, key: str, value: Any) -> None:
        self.key = value


LineIgnores = List[LineIgnore]
FileIgnores = Dict[str, LineIgnores]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dev", action="store_true", help="Creating the error file and not deleting it"
)
parser.add_argument(
    "--test",
    action="store_true",
    help="Reusing existing error file and not deleting it",
)
parser.add_argument("--log", action="store_true", help="Log details")
args = parser.parse_args()

if args.dev:
    SHOULD_GENERATE_ERROR_FILE = True
    SHOULD_DELETE_ERROR_FILE = False
    print("Running in dev mode, creating the file and not deleting it")
elif args.test:
    SHOULD_GENERATE_ERROR_FILE = False
    SHOULD_DELETE_ERROR_FILE = False
    print("Running in test mode, will reuse existing error file")
else:
    SHOULD_GENERATE_ERROR_FILE = True
    SHOULD_DELETE_ERROR_FILE = True

LOG = args.log


HERE = Path(__file__).parent.resolve()

# TODO: move into a JSON or other config file
# Files need to have a relative location to the directory of this file (/python)
file_specific_ignores = {
    "tools/helloworld.py": (
        {"rule": "reportMissingParameterType"},
        {"rule": "reportGeneralTypeIssues"},
        {
            "substring": 'Argument of type "Literal[3]" cannot be assigned to parameter "__k" of type "str"'
        },
    ),
    "tools/firmware-fingerprint.py": (
        {"rule": "reportMissingParameterType"},
        {"rule": "reportGeneralTypeIssues"},
        {
            "substring": 'Operator "+" not supported for types "Literal[3]" and "Literal['
        },
    ),
}


class PyrightTool:
    def __init__(self) -> None:
        self.ERROR_FILE = "errors_for_pyright_temp.json"

        self.PYRIGHT_CONFIG_FILE = HERE / "pyrightconfig.json"

        self.ON_PATTERN = "# pyright: on"
        self.OFF_PATTERN = "# pyright: off"
        self.IGNORE_PATTERN = "# pyright: ignore "
        self.IGNORE_DELIMITER = ";;"

        self.count_of_ignored_errors = 0

        self.file_specific_ignores = {
            str(HERE / k): v for k, v in file_specific_ignores.items()
        }

        all_files_to_check = self.get_all_files_to_check()
        self.all_pyright_ignores = self.get_all_pyright_ignores(all_files_to_check)

    def run(self) -> None:
        """Main function, putting together all logic and evaluating result"""
        original_pyright_errors = self.get_original_pyright_errors()
        real_errors = self.get_all_real_errors(original_pyright_errors)

        has_unused_ignores = self.check_for_unused_ignores()

        print(
            f"\nIgnored {self.count_of_ignored_errors} custom-defined errors from {len(self.all_pyright_ignores)} files."
        )
        if len(real_errors) == 0:
            print("Everything is fine!")
            if has_unused_ignores:
                print("But we have unused ignores!")
                sys.exit(1)
            else:
                sys.exit(0)
        else:
            print("We have issues!\n")
            for error in real_errors:
                self.print_human_readable_error(error)
            print(f"Found {len(real_errors)} issues above")
            if has_unused_ignores:
                print("And we have unused ignores!")
            sys.exit(1)

    def get_original_pyright_errors(self) -> Errors:
        """Extract error objects from pyright"""
        # TODO: probably make this cleaner and less hacky
        if SHOULD_GENERATE_ERROR_FILE:
            os.system(f"pyright --outputjson > {self.ERROR_FILE}")

        data = json.loads(open(self.ERROR_FILE, "r").read())

        if SHOULD_DELETE_ERROR_FILE:
            os.system(f"rm {self.ERROR_FILE}")

        return data["generalDiagnostics"]

    def get_all_real_errors(self, original_pyright_errors: Errors) -> Errors:
        """Analyze all pyright errors and discard all that should be ignored.

        Ignores can be different:
        - as per "# pyright: ignore [<error_substring>]" comment
        - as per "file_specific_ignores"
        - as per "# pyright: off" mark
        """
        real_errors: Errors = []
        for error in original_pyright_errors:
            # Special handling of cycle import issues, which have different format
            if "range" not in error:
                error["range"] = {"start": {"line": 0}}
                error["rule"] = "cycleImport"
                real_errors.append(error)
                continue

            file_path = error["file"]
            error_message = error["message"]
            line_no = error["range"]["start"]["line"]

            if self.should_ignore_file_specific_error(file_path, error):
                self.count_of_ignored_errors += 1
                self.log_ignore(error, "file specific error")
                continue

            if self.is_pyright_disabled_for_this_line(file_path, line_no):
                self.count_of_ignored_errors += 1
                self.log_ignore(error, "pyright disabled for this line")
                continue

            # file_ignores = self.get_pyright_ignores_from_file(file_path)
            file_ignores = self.all_pyright_ignores[file_path]

            # TOOO: could be made simpler/more efficient
            should_be_ignored = False
            for ignore_index, ignore in enumerate(file_ignores):
                if line_no == ignore.line_no:
                    for substring_index, ignore_statement in enumerate(
                        ignore.ignore_statements
                    ):
                        if ignore_statement.substring in error_message:
                            should_be_ignored = True
                            self.count_of_ignored_errors += 1
                            self.log_ignore(error, "error substring matched")
                            self.all_pyright_ignores[file_path][
                                ignore_index
                            ].ignore_statements[substring_index].already_used = True

            if not should_be_ignored:
                real_errors.append(error)

        return real_errors

    def get_all_files_to_check(self) -> Set[str]:
        """Get all files to be analyzed by pyright, based on its config"""
        all_files: Set[str] = set()
        data = json.loads(open(self.PYRIGHT_CONFIG_FILE, "r").read())

        if "include" in data:
            for folder_or_file in data["include"]:
                for file in self.get_all_py_files_recursively(folder_or_file):
                    all_files.add(file)
        else:
            # "include" is missing, we should analyze all files in root dir
            for file in self.get_all_py_files_recursively("."):
                all_files.add(file)

        if "exclude" in data:
            for folder_or_file in data["exclude"]:
                for file in self.get_all_py_files_recursively(folder_or_file):
                    if file in all_files:
                        all_files.remove(file)

        return all_files

    @staticmethod
    def get_all_py_files_recursively(folder_or_file: str) -> Set[str]:
        """Return all python files in certain folder (or the file itself)"""
        if os.path.isfile(folder_or_file):
            return set(str(HERE / folder_or_file))

        all_files: Set[str] = set()
        for root, _, files in os.walk(folder_or_file):
            for file in files:
                if file.endswith(".py"):
                    all_files.add(str(HERE / os.path.join(root, file)))

        return all_files

    def get_all_pyright_ignores(self, all_files_to_check: Set[str]) -> FileIgnores:
        """Get ignore information from all the files to be analyzed"""
        file_ignores: FileIgnores = {}
        for file in all_files_to_check:
            ignores = self.get_pyright_ignores_from_file(file)
            if ignores:
                file_ignores[file] = ignores

        return file_ignores

    def check_for_unused_ignores(self) -> bool:
        """Evaluate if there are no ignores not matched by existing pyright errors"""
        unused_ignores: List[str] = []
        for file, file_ignores in self.all_pyright_ignores.items():
            for line_ignore in file_ignores:
                for ignore_statement in line_ignore.ignore_statements:
                    if not ignore_statement.already_used:
                        err = f"file {file} has unused ignore at line {line_ignore.line_no} - {ignore_statement.substring}"
                        unused_ignores.append(err)

        if unused_ignores:
            print("THERE ARE UNUSED IGNORES!!")
            print(unused_ignores)

        return bool(unused_ignores)

    def should_ignore_file_specific_error(self, file: str, error: Error) -> bool:
        """Check if file has some overall ignore either in rule or in substring"""
        if file not in self.file_specific_ignores:
            return False

        for ignore_object in self.file_specific_ignores[file]:
            if "rule" in ignore_object:
                if error["rule"] == ignore_object["rule"]:
                    return True
            elif "substring" in ignore_object:
                if ignore_object["substring"] in error["message"]:
                    return True

        return False

    def is_pyright_disabled_for_this_line(self, file: str, line_no: int) -> bool:
        """Check if line is not in block of code disabled by # pyright: off"""
        # TODO: we could have a function returning ranges of enabled/disabled lines
        with open(file, "r") as f:
            pyright_off = False
            for index, line in enumerate(f):
                if index == line_no:
                    return pyright_off
                if self.OFF_PATTERN in line:
                    pyright_off = True
                elif self.ON_PATTERN in line:
                    pyright_off = False

        return False

    def get_pyright_ignores_from_file(self, file: str) -> LineIgnores:
        """Get all ignore lines and statements from a certain file"""
        ignores: LineIgnores = []
        with open(file, "r") as f:
            for index, line in enumerate(f):
                if self.IGNORE_PATTERN in line:
                    ignore_statements = self.get_ignore_statements(line)
                    ignores.append(LineIgnore(index, ignore_statements))

        return ignores

    def get_ignore_statements(self, line: str) -> List[IgnoreStatement]:
        """Extract error substrings to be ignored from a certain line"""
        # TODO: could make some regex instead
        statement_substrings = (
            line.split(self.IGNORE_PATTERN)[1]
            .strip(" []\n")
            .split(self.IGNORE_DELIMITER)
        )

        return [IgnoreStatement(substr) for substr in statement_substrings]

    def print_human_readable_error(self, error: Error) -> None:
        """Show a human-readable form of uncaught error"""
        print(self.get_human_readable_error_string(error))

    def log_ignore(self, error: Error, reason: str) -> None:
        """Print the action of ignoring certain error into the console"""
        if LOG:
            err = self.get_human_readable_error_string(error)
            to_log = f"\nError ignored. Reason: {reason}.\nErr: {err}"
            print(to_log)

    @staticmethod
    def get_human_readable_error_string(error: Error) -> str:
        """Transform error object to a string readable by human"""
        file = error["file"]
        message = error["message"]
        rule = error["rule"]
        line = error["range"]["start"]["line"]

        # Need to add +1 to the line, as it is zero-based index
        return f"{file}:{line + 1}: - error: {message} ({rule})\n"


if __name__ == "__main__":
    tool = PyrightTool()
    tool.run()
