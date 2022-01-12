import re
from typing import Dict, List
from collections import OrderedDict

FILES = ["build.yml"]
NOT_JOBS = [
    "variables:",
    "image:",
]
ALL_JOBS = OrderedDict()

DOC_FILE = "trial_docs.md"


def get_jobs_from_file(file: str) -> Dict[str, List[str]]:
    # TODO: we could also get overall description of the file/stage, located at the top of the file
    all_jobs = OrderedDict()
    job_name = ""  # indicates we identified a job and we want to read the comments belonging to it
    job_description_buffer = []

    # Looping through lines in reversed order, first identifying the job definition
    # and then loading all the comments above it.
    with open(file, "r") as f:
        for line in reversed(f.readlines()):
            line = line.rstrip()
            if job_name:
                # Search for comments
                # If comment not found, save all what we got
                if re.search(r"\A#", line):
                    # Deleting the comment from the beginning
                    job_description_buffer.append(re.sub(r"\A#+\s+", "", line))
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
                    # Getting rid of final ":"
                    job_name = line.rstrip(":")

    # To maintain the real order, we need to reverse the jobs, as they were read from the end
    return OrderedDict(reversed(all_jobs.items()))


def save_docs_into_file() -> None:
    with open(DOC_FILE, "w") as doc_file:
        for file in FILES:
            # TODO: we could even create a link pointing to this file
            doc_file.write(f"## {file}\n\n")
            for job_name, job_desc in ALL_JOBS[file].items():
                doc_file.write(f"### {job_name}\n")
                if not job_desc:
                    doc_file.write("Missing description\n")
                for line in job_desc:
                    doc_file.write(f"{line}\n")
                doc_file.write("\n")

            doc_file.write("\n")


if __name__ == "__main__":
    for file in FILES:
        file_jobs = get_jobs_from_file(file)
        ALL_JOBS[file] = file_jobs

    import json
    print(json.dumps(ALL_JOBS, indent=4))

    save_docs_into_file()
