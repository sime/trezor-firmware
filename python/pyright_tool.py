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
- ignoring of specific rules and error substrings for specific files/blocks of code
- report unused ignores
- some optional logging

ISSUES:
- "# pyright: ignore" is not understood by `black` as a type comment, so it is being affected
    and restyled - we might have to use "# type: ignore" instead
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

Error = Dict[str, Any]
Errors = List[Error]

IgnoreStatements = List[str]
Ignore = Tuple[int, IgnoreStatements]
Ignores = List[Ignore]

# Set False for development purposes (after getting the error file)
if len(sys.argv) > 1 and "test" in sys.argv[1]:
    SHOULD_GENERATE_ERROR_FILE_AND_CLEAN_IT = False
    print("Running in test mode, will reuse existing error file")
else:
    SHOULD_GENERATE_ERROR_FILE_AND_CLEAN_IT = True

HERE = Path(__file__).parent.resolve()

# TODO: move into a JSON or other config file
# Files need to have a relative location to the directory of this file (/python)
file_specific_ignores = {
    "tools/helloworld.py": (
        {"rule": "reportMissingParameterType"},
        {"rule": "reportGeneralTypeIssues"},
        {"substring": 'Argument of type "Literal[3]" cannot be assigned to parameter "__k" of type "str"'},
    ),
    "tools/firmware-fingerprint.py": (
        {"rule": "reportMissingParameterType"},
        {"rule": "reportGeneralTypeIssues"},
        {"substring": 'Operator "+" not supported for types "Literal[3]" and "Literal['},
    ),
}


class PyrightTool:
    def __init__(self) -> None:
        self.ERROR_FILE = "errors_for_pyright_temp.json"

        self.IGNORE_PATTERN = "# pyright: ignore "
        self.IGNORE_DELIMITER = ";;"

        self.count_of_ignored_errors = 0

        self.file_specific_ignores = {
            str(HERE / k): v for k, v in file_specific_ignores.items()
        }

    def run(self) -> None:
        original_pyright_errors = self.get_original_pyright_errors()
        real_errors = self.get_all_real_errors(original_pyright_errors)

        print(f"\nIgnored {self.count_of_ignored_errors} custom-defined errors.")
        if len(real_errors) == 0:
            print("Everything is fine!")
            sys.exit(0)
        else:
            print("We have issues!\n")
            for error in real_errors:
                self.print_human_readable_error(error)
            print(f"Found {len(real_errors)} issues above")
            sys.exit(1)

    def get_original_pyright_errors(self) -> Errors:
        # TODO: probably make this cleaner and less hacky
        if SHOULD_GENERATE_ERROR_FILE_AND_CLEAN_IT:
            os.system(f"pyright --outputjson > {self.ERROR_FILE}")

        data = json.loads(open(self.ERROR_FILE, "r").read())

        if SHOULD_GENERATE_ERROR_FILE_AND_CLEAN_IT:
            os.system(f"rm {self.ERROR_FILE}")

        return data["generalDiagnostics"]

    def get_all_real_errors(self, original_pyright_errors: Errors) -> Errors:
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
                continue

            file_ignores = self.get_pyright_ignores_from_file(file_path)

            # TOOO: could be made simpler/more efficient
            should_be_ignored = False
            for line_index, ignore_strings in file_ignores:
                if line_no == line_index:
                    for ignore_string in ignore_strings:
                        if ignore_string in error_message:
                            should_be_ignored = True
                            self.count_of_ignored_errors += 1

            if not should_be_ignored:
                real_errors.append(error)

        return real_errors

    def should_ignore_file_specific_error(self, file: str, error: Error) -> bool:
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

    def get_pyright_ignores_from_file(self, file: str) -> Ignores:
        # TODO: have a cache for files when we ask multiple times for the same file
        ignores: Ignores = []
        with open(file, "r") as f:
            for index, line in enumerate(f):
                if self.IGNORE_PATTERN in line:
                    ignore_statements = self.get_ignore_statements(line)
                    ignores.append((index, ignore_statements))

        return ignores

    def get_ignore_statements(self, line: str) -> IgnoreStatements:
        # TODO: could make some regex instead
        return (
            line.split(self.IGNORE_PATTERN)[1]
            .strip(" []\n")
            .split(self.IGNORE_DELIMITER)
        )

    @staticmethod
    def print_human_readable_error(error: Error) -> None:
        file = error["file"]
        message = error["message"]
        rule = error["rule"]
        line = error["range"]["start"]["line"]

        # Need to add +1 to the line, as it is zero-based index
        print(f"{file}:{line + 1}: - error: {message} ({rule})\n")


if __name__ == "__main__":
    tool = PyrightTool()
    tool.run()
