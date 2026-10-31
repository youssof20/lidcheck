"""Use the existing Git credential helper without logging credentials."""

import argparse
import json
import subprocess
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    )
    credential = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    headers = {
        "Authorization": "Bearer " + credential["password"],
        "Accept": "application/vnd.github+json",
        "User-Agent": "lidcheck-build",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = "https://api.github.com/repos/youssof20/lidcheck"

    def request(path: str, method: str = "GET", data: dict | None = None) -> dict:
        req = urllib.request.Request(
            base + path,
            headers=headers,
            method=method,
            data=json.dumps(data).encode() if data is not None else None,
        )
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    repo = request("")
    print("Repository visibility:", repo["visibility"])
    if repo["private"] and args.public:
        request("", "PATCH", {"private": False})
        print("Set repository public as required by the build brief")
    elif repo["private"]:
        raise RuntimeError("Repository is private; Pages brief requires public visibility")
    if args.enable:
        try:
            request("/pages", "POST", {"build_type": "workflow"})
        except urllib.error.HTTPError as error:
            if error.code == 409:
                request("/pages", "PUT", {"build_type": "workflow"})
            else:
                raise
    try:
        page = request("/pages")
        print(
            "Pages:",
            page["html_url"],
            "status:",
            page.get("status"),
            "build type:",
            page.get("build_type"),
        )
    except urllib.error.HTTPError as error:
        print("Pages API status:", error.code)
    runs = request("/actions/runs?per_page=6")
    for run in runs["workflow_runs"]:
        print(run["name"], run["status"], run["conclusion"], run["html_url"])


if __name__ == "__main__":
    main()
