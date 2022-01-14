import argparse
import filecmp
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

import yaml

# TODO: could read sections inside the file with some overall description of below jobs
# TODO: could add something like "Generated automatically, do not edit by hand" into the README

parser = argparse.ArgumentParser()
parser.add_argument(
    "--test",
    action="store_true",
    help="Check if there are no new changes in all CI .yml files",
)
args = parser.parse_args()


class DocsGenerator:
    def __init__(self) -> None:
        # Navigating ourselves to the root directory, so the relative
        # locations of CI files are valid
        os.chdir(Path(__file__).parent.resolve().parent.resolve())

        self.GITLAB_CI_FILE = ".gitlab-ci.yml"
        self.DOC_FILE = "ci/trial_docs.md"

        # Some keywords that are not job definitions and we should not care about them
        self.NOT_JOBS = [
            "variables:",
            "image:",
        ]

        self.ALL_JOBS = OrderedDict()

        self.FILES = self.get_all_ci_files()
        print("FILES", self.FILES)

    def generate_docs(self) -> None:
        """Whole pipeline of getting and saving the CI information."""
        for file in self.FILES:
            file_info = {}
            file_info["jobs"] = self.get_jobs_from_file(file)
            file_info["overall_description"] = self.get_overall_description_from_file(
                file
            )
            self.ALL_JOBS[file] = file_info

        self.save_docs_into_file()

    def verify_docs(self) -> None:
        """Checking if the docs are up-to-date with current CI .yml files.

        Creating a new doc file and comparing it against already existing one.
        Exit with non-zero exit code when these files do not match.
        """
        already_filled_doc_file = self.DOC_FILE
        self.DOC_FILE = "new_file.md"

        try:
            self.generate_docs()
            if not filecmp.cmp(already_filled_doc_file, self.DOC_FILE):
                print("The content of CI .yml files does not correspond to README file")
                sys.exit(1)
        finally:
            os.remove(self.DOC_FILE)

    def get_all_ci_files(self) -> List[str]:
        """Loading all the CI files which are used in Gitlab."""
        if not os.path.exists(self.GITLAB_CI_FILE):
            raise RuntimeError(
                f"Main Gitlab CI file under {self.GITLAB_CI_FILE} does not exist!"
            )

        with open(self.GITLAB_CI_FILE, "r") as f:
            gitlab_file_content = yaml.safe_load(f)

        all_ci_files = gitlab_file_content["include"]

        for file in all_ci_files:
            if not os.path.isfile(file):
                raise RuntimeError(f"File {file} does not exist!")

        return all_ci_files

    @staticmethod
    def get_overall_description_from_file(file: str) -> List[str]:
        """Looking for comments at the very beginning of the file."""
        description_lines = []
        with open(file, "r") as f:
            for line in f:
                if line.startswith("#"):
                    # Taking just the text - no hashes, no whitespace
                    description_lines.append(line.strip("# \n"))
                else:
                    break

        return description_lines

    def get_jobs_from_file(self, file: str) -> Dict[str, Dict[str, Any]]:
        """Extract all jobs and their details from a certain file."""
        all_jobs: Dict[str, Dict[str, Any]] = OrderedDict()

        # Taking all the comments above a non-indented non-comment, which is
        # always a job definition, unless defined in NOT_JOBS
        with open(file, "r") as f:
            comment_buffer = []
            for index, line in enumerate(f):
                if line.startswith("#"):
                    # Taking just the text - no hashes, no whitespace
                    comment_buffer.append(line.strip("# \n"))
                else:
                    if re.search(r"\A\w", line) and not any(
                        [line.startswith(not_job) for not_job in self.NOT_JOBS]
                    ):
                        job_name = line.rstrip(":\n")
                        all_jobs[job_name] = {
                            "description": comment_buffer,
                            "line_no": index + 1,
                        }
                    comment_buffer = []

        return all_jobs

    def save_docs_into_file(self) -> None:
        """Dump all the information into a documentation file."""
        with open(self.DOC_FILE, "w") as doc_file:
            # Some general info for the whole CI
            doc_file.write("# CI pipeline\n")
            doc_file.write(
                "It consists of multiple stages below, each having one or more jobs\n"
            )
            latest_master = "https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/pipelines/master/latest"
            doc_file.write(
                f"Latest CI pipeline of master branch can be seen at [{latest_master}]({latest_master})\n"
            )

            # TODO: test-hw are run inside test stage, maybe unite it under i
            for file, file_info in self.ALL_JOBS.items():
                # Generating header with a link to the file
                doc_file.write(
                    f"## {Path(file).stem.upper()} stage - [file](../{file})\n\n"
                )

                # TODO: are we alright using this python >= 3.8 feature (walrus operator)?
                if description := file_info["overall_description"]:
                    for line in description:
                        doc_file.write(f"{line}\n")
                    doc_file.write("\n")

                job_amount = f"{len(file_info['jobs'])} job{'s' if len(file_info['jobs']) > 1 else ''}"
                doc_file.write(f"Consists of {job_amount} below\n")

                for job_name, job_info in file_info["jobs"].items():
                    # Generating smaller header with link to the exact line of
                    # this job in the master branch
                    # (will work properly only after merging changes to master)
                    github_job_link = f"https://github.com/trezor/trezor-firmware/blob/master/{file}#L{job_info['line_no']}"
                    doc_file.write(f"- ### [{job_name}]({github_job_link})\n")
                    if not job_info["description"]:
                        doc_file.write("Missing description\n")
                    for line in job_info["description"]:
                        doc_file.write(f"{line}\n")
                    doc_file.write("\n")

                doc_file.write("---")
                doc_file.write("\n")


if __name__ == "__main__":
    if args.test:
        DocsGenerator().verify_docs()
    else:
        DocsGenerator().generate_docs()
