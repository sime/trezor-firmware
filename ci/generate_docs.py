import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Navigating ourselves to the root directory, so the relative
# locations of CI files are valid
HERE = Path(__file__).parent.resolve()
ROOT_DIR = HERE.parent.resolve()
os.chdir(ROOT_DIR)

GITLAB_CI_FILE = ".gitlab-ci.yml"
DOC_FILE = "ci/trial_docs.md"

# Loading all the CI files which are used in Gitlab
with open(GITLAB_CI_FILE, "r") as f:
    content = yaml.safe_load(f)
    FILES = content["include"]
    print("FILES", FILES)

# Some keywords that are not job definitions and we should not care about them
NOT_JOBS = [
    "variables:",
    "image:",
]

ALL_JOBS = OrderedDict()


# TODO: could read sections inside the file with some overall description of below jobs
# TODO: could create a --test argument checking that the docs are up-to-date


def get_overall_description_from_file(file: str) -> List[str]:
    # Looking for comments at the very beginning of the file
    description_lines = []
    with open(file, "r") as f:
        for line in f:
            if line.startswith("#"):
                # Taking just the text - no hashes, no whitespace
                description_lines.append(line.strip("# \n"))
            else:
                break

    return description_lines


def get_jobs_from_file(file: str) -> Dict[str, Dict[str, Any]]:
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
                    [line.startswith(not_job) for not_job in NOT_JOBS]
                ):
                    job_name = line.rstrip(":\n")
                    all_jobs[job_name] = {
                        "description": comment_buffer,
                        "line_no": index + 1,
                    }
                comment_buffer = []

    return all_jobs


def save_docs_into_file() -> None:
    with open(DOC_FILE, "w") as doc_file:
        for file, file_info in ALL_JOBS.items():
            # Generating header with a link to the file
            doc_file.write(f"## [{file}](../{file})\n\n")

            # TODO: are we alright using this python >= 3.8 feature (walrus operator)?
            if description := file_info["overall_description"]:
                for line in description:
                    doc_file.write(f"{line}\n")
                doc_file.write("\n")

            for job_name, job_info in file_info["jobs"].items():
                # Generating smaller header with link to the exact line of
                # this job in the master branch
                # (will work properly only after merging changes to master)
                github_link = "https://github.com/trezor/trezor-firmware/blob/master"
                doc_file.write(
                    f"### [{job_name}]({github_link}/{file}#L{job_info['line_no']})\n"
                )
                if not job_info["description"]:
                    doc_file.write("Missing description\n")
                for line in job_info["description"]:
                    doc_file.write(f"{line}\n")
                doc_file.write("\n")

            doc_file.write("---")
            doc_file.write("\n")


if __name__ == "__main__":
    for file in FILES:
        file_info = {}
        file_info["jobs"] = get_jobs_from_file(file)
        file_info["overall_description"] = get_overall_description_from_file(file)
        ALL_JOBS[file] = file_info

    # import json
    # print(json.dumps(ALL_JOBS, indent=4))

    save_docs_into_file()
