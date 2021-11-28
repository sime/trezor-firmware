"""
Wrapper around pyright type checking to allow us for easy inline
ignore of specific error messages.

Usage:
- there are multiple ways how to ignore/silence a pyright error:
    - "# pyright: ignore [<error_substring>]"
        - put it as a comment to the line we want to ignore
        - "# pyright: ignore [<error1>;;<error2>;;...]" if there are more than one errors on that line
    - "# pyright: off" / "# pyright: on"
        - all errors in block of code between these marks will be ignored
    - FILE_SPECIFIC_IGNORES
        - ignore specific rules (defined by pyright) or error substrings in the whole file

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
from typing import Dict, List, Set, TypedDict, Union


class RangeDetail(TypedDict):
    line: int
    character: int


class Range(TypedDict):
    start: RangeDetail
    end: RangeDetail


class Error(TypedDict):
    file: str
    severity: str
    message: str
    range: Range
    rule: str


Errors = List[Error]


class Summary(TypedDict):
    filesAnalyzed: int
    errorCount: int
    warningCount: int
    informationCount: int
    timeInSec: float


class PyrightResults(TypedDict):
    version: str
    time: str
    generalDiagnostics: Errors
    summary: Summary


@dataclass
class IgnoreStatement:
    substring: str
    already_used: bool = False


@dataclass
class LineIgnore:
    line_no: int
    ignore_statements: List[IgnoreStatement]


LineIgnores = List[LineIgnore]
FileIgnores = Dict[str, LineIgnores]


@dataclass
class FileSpecificIgnore:
    rule: str = ""
    substring: str = ""
    already_used: bool = False

    def __post_init__(self):
        if self.rule and self.substring:
            raise ValueError("Only one of rule|substring should be set")


FileSpecificIgnores = Dict[str, List[FileSpecificIgnore]]

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
    should_generate_error_file = True
    should_delete_error_file = False
    print("Running in dev mode, creating the file and not deleting it")
elif args.test:
    should_generate_error_file = False
    should_delete_error_file = False
    print("Running in test mode, will reuse existing error file")
else:
    should_generate_error_file = True
    should_delete_error_file = True

SHOULD_GENERATE_ERROR_FILE = should_generate_error_file
SHOULD_DELETE_ERROR_FILE = should_delete_error_file
SHOULD_LOG = args.log

HERE = Path(__file__).parent.resolve()

# TODO: move into a JSON or other config file
# Files need to have a relative location to the directory of this file (/python)
FILE_SPECIFIC_IGNORES = {
    "tools/helloworld.py": [
        FileSpecificIgnore(rule="reportMissingParameterType"),
        FileSpecificIgnore(rule="reportGeneralTypeIssues"),
        FileSpecificIgnore(
            substring='Argument of type "Literal[3]" cannot be assigned to parameter "__k" of type "str"'
        ),
    ],
    "tools/firmware-fingerprint.py": [
        FileSpecificIgnore(
            substring='Operator "+" not supported for types "Literal[3]" and "Literal['
        ),
    ],
}

# Putting substrings at the beginning of ignore-lists, so they are matched before rules
# (Not to leave them potentially unused when error would be matched by a rule instead)
for file in FILE_SPECIFIC_IGNORES:
    FILE_SPECIFIC_IGNORES[file].sort(key=lambda x: x.substring, reverse=True)


class PyrightTool:
    ON_PATTERN = "# pyright: on"
    OFF_PATTERN = "# pyright: off"
    IGNORE_PATTERN = "# pyright: ignore "
    IGNORE_DELIMITER = ";;"

    original_pyright_results: PyrightResults
    all_files_to_check: Set[str]
    all_pyright_ignores: FileIgnores
    real_errors: Errors
    unused_ignores: List[str]

    def __init__(
        self,
        file_specific_ignores: FileSpecificIgnores,
        pyright_config_file: Union[str, Path],
        error_file: Union[str, Path],
        should_generate_error_file: bool,
        should_delete_error_file: bool,
        should_log: bool = False,
    ) -> None:
        self.file_specific_ignores = file_specific_ignores
        self.pyright_config_file = pyright_config_file
        self.error_file = error_file
        self.should_generate_error_file = should_generate_error_file
        self.should_delete_error_file = should_delete_error_file
        self.should_log = should_log

        self.count_of_ignored_errors = 0

    def run(self) -> None:
        """Main function, putting together all logic and evaluating result."""
        self.original_pyright_results = self.get_original_pyright_results()

        self.all_files_to_check = self.get_all_files_to_check()
        self.all_pyright_ignores = self.get_all_pyright_ignores()

        self.real_errors = self.get_all_real_errors()
        self.unused_ignores = self.get_unused_ignores()

        self.evaluate_final_result()

    def evaluate_final_result(self) -> None:
        """Reporting results to the user/CI (printing stuff, deciding exit value)."""
        print(
            f"\nIgnored {self.count_of_ignored_errors} custom-defined errors "
            f"from {len(self.all_pyright_ignores)} files."
        )

        if self.unused_ignores:
            print("\nWARNING: there are unused ignores!")
            for unused_ignore in self.unused_ignores:
                print(unused_ignore)

        if not self.real_errors:
            print("\nSUCCESS: Everything is fine!")
            if self.unused_ignores:
                print("But we have unused ignores!")
                sys.exit(2)
            else:
                sys.exit(0)
        else:
            print("\nERROR: We have issues!\n")
            for error in self.real_errors:
                self.print_human_readable_error(error)
            print(f"Found {len(self.real_errors)} issues above")
            if self.unused_ignores:
                print("And we have unused ignores!")
            sys.exit(1)

    def get_original_pyright_results(self) -> PyrightResults:
        """Extract all information from pyright.

        `pyright --outputjson` will return all the results in
        nice JSON format with `generalDiagnostics` array storing
        all the errors - schema described in PyrightResults
        """
        # TODO: probably make this cleaner and less hacky
        if self.should_generate_error_file:
            os.system(f"pyright --outputjson > {self.error_file}")
            print(80 * "*")

        pyright_results: PyrightResults = json.loads(open(self.error_file, "r").read())

        if self.should_delete_error_file:
            os.system(f"rm {self.error_file}")

        return pyright_results

    def get_all_real_errors(self) -> Errors:
        """Analyze all pyright errors and discard all that should be ignored.

        Ignores can be different:
        - as per "# pyright: ignore [<error_substring>]" comment
        - as per "file_specific_ignores"
        - as per "# pyright: off" mark
        """
        real_errors: Errors = []
        for error in self.original_pyright_results["generalDiagnostics"]:
            # Special handling of cycle import issues, which have different format
            if "range" not in error:
                error["range"] = {"start": {"line": 0}}
                error["rule"] = "cycleImport"
                real_errors.append(error)
                continue

            file_path = error["file"]
            error_message = error["message"]
            line_no = error["range"]["start"]["line"]

            # Checking in file_specific_ignores
            if self.should_ignore_file_specific_error(file_path, error):
                self.count_of_ignored_errors += 1
                self.log_ignore(error, "file specific error")
                continue

            # Checking for "# pyright: off" mark
            if self.is_pyright_disabled_for_this_line(file_path, line_no):
                self.count_of_ignored_errors += 1
                self.log_ignore(error, "pyright disabled for this line")
                continue

            # File with issue might not have any pyright: ignores
            if file_path not in self.all_pyright_ignores:
                real_errors.append(error)
                continue

            # Checking for "# pyright: ignore [<error_substring>]" comment
            # TOOO: could be made simpler/more efficient
            file_ignores = self.all_pyright_ignores[file_path]
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
                            # Marking this ignore to be used (so we can identify unused ignores)
                            self.all_pyright_ignores[file_path][
                                ignore_index
                            ].ignore_statements[substring_index].already_used = True

            if not should_be_ignored:
                real_errors.append(error)

        return real_errors

    def get_all_files_to_check(self) -> Set[str]:
        """Get all files to be analyzed by pyright, based on its config."""
        all_files: Set[str] = set()
        config_data = json.loads(open(self.pyright_config_file, "r").read())

        if "include" in config_data:
            for folder_or_file in config_data["include"]:
                for file in self.get_all_py_files_recursively(folder_or_file):
                    all_files.add(file)
        else:
            # "include" is missing, we should analyze all files in root dir
            for file in self.get_all_py_files_recursively("."):
                all_files.add(file)

        if "exclude" in config_data:
            for folder_or_file in config_data["exclude"]:
                for file in self.get_all_py_files_recursively(folder_or_file):
                    if file in all_files:
                        all_files.remove(file)

        return all_files

    @staticmethod
    def get_all_py_files_recursively(folder_or_file: str) -> Set[str]:
        """Return all python files in certain folder (or the file itself)."""
        if os.path.isfile(folder_or_file):
            return set(str(HERE / folder_or_file))

        all_files: Set[str] = set()
        for root, _, files in os.walk(folder_or_file):
            for file in files:
                if file.endswith(".py"):
                    all_files.add(str(HERE / os.path.join(root, file)))

        return all_files

    def get_all_pyright_ignores(self) -> FileIgnores:
        """Get ignore information from all the files to be analyzed."""
        file_ignores: FileIgnores = {}
        for file in self.all_files_to_check:
            ignores = self.get_pyright_ignores_from_file(file)
            if ignores:
                file_ignores[file] = ignores

        return file_ignores

    def get_unused_ignores(self) -> List[str]:
        """Evaluate if there are no ignores not matched by existing pyright errors."""
        unused_ignores: List[str] = []

        for file, file_ignores in self.all_pyright_ignores.items():
            for line_ignore in file_ignores:
                for ignore_statement in line_ignore.ignore_statements:
                    if not ignore_statement.already_used:
                        unused_ignores.append(
                            f"File {file} has unused ignore at line {line_ignore.line_no + 1}. "
                            f"Substring: {ignore_statement.substring}"
                        )

        for file, file_ignores in self.file_specific_ignores.items():
            for ignore_object in file_ignores:
                if not ignore_object.already_used:
                    if ignore_object.substring:
                        unused_ignores.append(
                            f"File {file} has unused specific ignore substring. "
                            f"Substring: {ignore_object.substring}"
                        )
                    elif ignore_object.rule:
                        unused_ignores.append(
                            f"File {file} has unused specific ignore rule. "
                            f"Rule: {ignore_object.rule}"
                        )

        return unused_ignores

    def should_ignore_file_specific_error(self, file: str, error: Error) -> bool:
        """Check if file has some overall ignore either in rule or in substring."""
        if file not in self.file_specific_ignores:
            return False

        for ignore_object in self.file_specific_ignores[file]:
            if ignore_object.rule:
                if error["rule"] == ignore_object.rule:
                    ignore_object.already_used = True
                    return True
            elif ignore_object.substring:
                if ignore_object.substring in error["message"]:
                    ignore_object.already_used = True
                    return True

        return False

    def is_pyright_disabled_for_this_line(self, file: str, line_no: int) -> bool:
        """Check if line is not in block of code disabled by # pyright: off."""
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
        """Get all ignore lines and statements from a certain file."""
        ignores: LineIgnores = []
        with open(file, "r") as f:
            for index, line in enumerate(f):
                if self.IGNORE_PATTERN in line:
                    ignore_statements = self.get_ignore_statements(line)
                    ignores.append(LineIgnore(index, ignore_statements))

        return ignores

    def get_ignore_statements(self, line: str) -> List[IgnoreStatement]:
        """Extract error substrings to be ignored from a certain line."""
        # TODO: could make some regex instead
        statement_substrings = (
            line.split(self.IGNORE_PATTERN)[1]
            .strip(" []\n")
            .split(self.IGNORE_DELIMITER)
        )

        return [IgnoreStatement(substr) for substr in statement_substrings]

    def print_human_readable_error(self, error: Error) -> None:
        """Show a human-readable form of uncaught error."""
        print(self.get_human_readable_error_string(error))

    def log_ignore(self, error: Error, reason: str) -> None:
        """Print the action of ignoring certain error into the console."""
        if self.should_log:
            err = self.get_human_readable_error_string(error)
            print(f"\nError ignored. Reason: {reason}.\nErr: {err}")

    @staticmethod
    def get_human_readable_error_string(error: Error) -> str:
        """Transform error object to a string readable by human."""
        file = error["file"]
        message = error["message"]
        rule = error["rule"]
        line = error["range"]["start"]["line"]

        # Need to add +1 to the line, as it is zero-based index
        return f"{file}:{line + 1}: - error: {message} ({rule})\n"


if __name__ == "__main__":
    tool = PyrightTool(
        file_specific_ignores={
            str(HERE / k): v for k, v in FILE_SPECIFIC_IGNORES.items()
        },
        pyright_config_file=HERE / "pyrightconfig.json",
        error_file="errors_for_pyright_temp.json",
        should_generate_error_file=SHOULD_GENERATE_ERROR_FILE,
        should_delete_error_file=SHOULD_DELETE_ERROR_FILE,
        should_log=SHOULD_LOG,
    )
    tool.run()
