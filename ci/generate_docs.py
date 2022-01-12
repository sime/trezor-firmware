import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List

import yaml

# Navigating ourselves to the root directory, so the relative
# locations of CI files are valid
HERE = Path(__file__).parent.resolve()
ROOT_DIR = HERE.parent.resolve()
os.chdir(ROOT_DIR)

GITLAB_CI_FILE = ".gitlab-ci.yml"
DOC_FILE = "ci/trial_docs.md"

with open(GITLAB_CI_FILE, "r") as f:
    content = yaml.safe_load(f)
    FILES = content["include"]
    print("FILES", FILES)

NOT_JOBS = [
    "variables:",
    "image:",
]
ALL_JOBS = OrderedDict()


# TODO: could read sections inside the file with some overall description of below jobs


def get_overall_description_from_file(file: str) -> List[str]:
    # Looking for comments at the very beginning of the file
    description_lines = []
    with open(file, "r") as f:
        for line in f:
            if line.startswith("#"):
                # Deleting the comment from the beginning
                description_lines.append(line.strip("# \n"))
            else:
                break

    return description_lines


def get_jobs_from_file(file: str) -> Dict[str, List[str]]:
    all_jobs = OrderedDict()
    job_name = ""  # indicates we identified a job and we want to read the comments belonging to it
    job_description_buffer = []

    # Looping through lines in reversed order, first identifying the job definition
    # and then loading all the comments above it.
    with open(file, "r") as f:
        for line in reversed(f.readlines()):
            if job_name:
                # Search for comments
                # If comment not found, save all what we got
                if line.startswith("#"):
                    # Deleting the comment from the beginning
                    job_description_buffer.append(line.strip("# \n"))
                else:
                    # Save and move on to another job
                    # All the description lines need to be reversed
                    all_jobs[job_name] = list(reversed(job_description_buffer))
                    job_description_buffer = []
                    job_name = ""
            else:
                # Looking for a non-indented line, which signals job definition
                if re.search(r"\A\w", line) and not any(
                    [line.startswith(not_job) for not_job in NOT_JOBS]
                ):
                    job_name = line.rstrip(":\n")

    # To maintain the real order, we need to reverse the jobs, as they were read from the end
    return OrderedDict(reversed(all_jobs.items()))


def save_docs_into_file() -> None:
    with open(DOC_FILE, "w") as doc_file:
        for file, file_info in ALL_JOBS.items():
            # TODO: we could even create a link pointing to this file
            doc_file.write(f"## {file}\n\n")

            # TODO: are we alright using this python >= 3.8 feature (walrus operator)?
            if description := file_info["overall_description"]:
                for line in description:
                    doc_file.write(f"{line}\n")
                doc_file.write("\n")

            for job_name, job_desc in file_info["jobs"].items():
                doc_file.write(f"### {job_name}\n")
                if not job_desc:
                    doc_file.write("Missing description\n")
                for line in job_desc:
                    doc_file.write(f"{line}\n")
                doc_file.write("\n")

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
