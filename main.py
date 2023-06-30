import json
import math
import os
import subprocess
import sys
from getpass import getpass
from os import path
import time
from typing import Optional, Tuple

import requests

# Optional values to configure
DEFAULT_OUTPUT_DIRECTORY = "output/"
COOKIE_CACHE_PATH = "cookie.txt"
PROMPT_FOR_COOKIE_CACHE = True

BACKOFF_START = 5  # This is the backoff we start at when we get an error
BACKOFF_INCREMENT = 5  # Every time we get an error, we increment by this amount of backoff before trying again

# Code begins here


# Define some util methods for getting input
def attempt_get_roblox_cookie():
    global PROMPT_FOR_COOKIE_CACHE
    roblox_cookie = None

    while True:
        # Load from cache, if allowed
        if PROMPT_FOR_COOKIE_CACHE and path.exists(COOKIE_CACHE_PATH):
            with open(COOKIE_CACHE_PATH, "r") as file:
                roblox_cookie = file.read()
                PROMPT_FOR_COOKIE_CACHE = False
                print(f"Roblox cookie: <Read from {COOKIE_CACHE_PATH}>")
                return roblox_cookie

        # Otherwise, try to get via user input
        roblox_cookie: str = getpass("Roblox cookie (.ROBLOSECURITY): ").strip()

        if len(roblox_cookie) > 0:
            break
        print("Invalid Roblox cookie, please try again!")

    # Prompt to cache cookie if user wants
    if PROMPT_FOR_COOKIE_CACHE:
        STORE_FOR_FUTURE = (
            input("Cache this cookie for future use (stored in cookie.txt)? (Y/N) ")
            .strip()
            .lower()
        )

        if STORE_FOR_FUTURE == "y" or STORE_FOR_FUTURE == "yes":
            with open(COOKIE_CACHE_PATH, "w") as file:
                file.write(roblox_cookie)

    return roblox_cookie


def attempt_get_positive_int(
    prompt: str, error_if_invalid: str, default_if_no_input: Optional[int] = None
) -> int:
    while True:
        raw_input: str = input(prompt).strip()

        if len(raw_input) == 0 and default_if_no_input is not None:
            return default_if_no_input

        value = None
        try:
            value: int = int(raw_input)
        except:
            pass

        if isinstance(value, int) and value > 0:
            return value

        print(error_if_invalid)


def attempt_get_bool(prompt: str, error_if_invalid: str) -> bool:
    while True:
        raw_input: str = input(prompt).strip().lower()

        if raw_input == "yes" or raw_input == "y":
            return True

        if raw_input == "no" or raw_input == "n":
            return False

        print(error_if_invalid)


# Utils
def run_command(
    command: str, cwd=".", env=None, error_on_failure=False, error_prefix=None
) -> subprocess.CompletedProcess[str]:
    result = None
    prefix = f"{error_prefix}" if error_prefix else ""

    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, env=env
        )
    except Exception as err:
        if error_on_failure:
            raise RuntimeError(f"{prefix}Failed to run `{command}`:\n{err}") from None

    if result and result.returncode != 0 and error_on_failure:
        raise RuntimeError(
            f"{prefix}Failed to run `{command}`, exit code {result.returncode}:\n{result.stderr}"
        )

    return result


# Validate git exists
run_command(
    "git --version",
    error_on_failure=True,
    error_prefix="Failed to validate git exists! Make sure git is installed! ",
)

# Check IF lune exists
lune = os.environ["ROBLOX_ARCHIVE_LUNE"]

if not lune or len(lune) == 0:
    lune = "lune"

lune_check_result = run_command(f"{lune} --version")
LUNE_EXISTS = lune_check_result and lune_check_result.returncode == 0

# Get the output path
OUTPUT_DIRECTORY = input(
    f"Output directory (default = {DEFAULT_OUTPUT_DIRECTORY}): "
).strip()

if len(OUTPUT_DIRECTORY) == 0:
    OUTPUT_DIRECTORY = DEFAULT_OUTPUT_DIRECTORY

if path.exists(OUTPUT_DIRECTORY):
    raise RuntimeError("Output path already exists! Cannot proceed.")

# Get the Roblox cookie
ROBLOX_COOKIE = attempt_get_roblox_cookie()

# Get the Place Id
PLACE_ID = attempt_get_positive_int("Place Id: ", "Invalid place id, please try again!")

# Get the minimum version
MIN_VERSION = attempt_get_positive_int(
    "Minimum version (default = 1): ",
    "Invalid minimum version, please try again!",
    1,
)

# Get the maximum version
MAX_VERSION = attempt_get_positive_int(
    "Maximum version (default = none): ",
    "Invalid maximum version, please try again!",
    sys.maxsize,
)

advanced = ""
LUNE_EXPAND_MODE = None
LUNE_EXPAND_PATH = path.join(path.dirname(path.abspath(__file__)), "expand.luau")

if LUNE_EXISTS:
    LUNE_RBXLX = attempt_get_bool(
        "Also output .rbxlx (y/n): ",
        'Please response with "y" or "n", try again!',
    )
    advanced += f"  Output .rbxlx too: {'yes' if LUNE_RBXLX else 'no'}\n"

    LUNE_FS_EXPAND = attempt_get_bool(
        "Also output scripts as .luau files (y/n): ",
        'Please response with "y" or "n", try again!',
    )
    advanced += (
        f"  Output scripts as .luau files: {'yes' if LUNE_FS_EXPAND else 'no'}\n"
    )

    if LUNE_RBXLX and LUNE_FS_EXPAND:
        LUNE_EXPAND_MODE = "all"
    elif LUNE_RBXLX and not LUNE_FS_EXPAND:
        LUNE_EXPAND_MODE = "rbxlx"
    elif not LUNE_RBXLX and LUNE_FS_EXPAND:
        LUNE_EXPAND_MODE = "fs_expand"
else:
    advanced = f"  Advanced options disabled because {lune} does not exist, this is optional, see README.md for more info\n"

# Print out all configs
print(
    f"\nFinal configuration:\n"
    + f"  Output directory: {OUTPUT_DIRECTORY}\n"
    + f"  Roblox cookie: ***\n"
    + f"  Place Id: {PLACE_ID}\n"
    + f"  Minimum version: {MIN_VERSION}\n"
    + f"  Maximum version: {MAX_VERSION if MAX_VERSION != sys.maxsize else 'none'}\n"
    + advanced
)

# All configs are defined, start initial setup

print("Creating directory...")
os.makedirs(OUTPUT_DIRECTORY)
run_command("git init", OUTPUT_DIRECTORY, error_on_failure=True)

COOKIES = {
    ".ROBLOSECURITY": ROBLOX_COOKIE,
}

# Get version metadata
version_metadata = {}

cursor = None
page = 1
metadata_max_version = -1
while True:
    print(f"Getting version metadata page {page}...")
    # Note that /saved-versions (undocumented) is a lot like /versions, but also
    response = requests.get(
        f"https://develop.roblox.com/v1/assets/{PLACE_ID}/saved-versions",
        {
            "limit": "50",
            "sortOrder": "Desc",
            "cursor": cursor,
        },
        headers={
            "Accept": "application/json",
        },
        cookies=COOKIES,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Error {response.status_code} on {response.url} occurred while getting version metadata:\n{response.text}"
        )

    json_response = response.json()

    for metadata in json_response["data"]:
        version = metadata["assetVersionNumber"]

        if int(version) > metadata_max_version:
            metadata_max_version = int(version)

        version_metadata[version] = metadata

    cursor = json_response["nextPageCursor"]

    if not cursor:
        break

    page += 1

print(f"Got version metadata for {metadata_max_version} versions")

# Go through each version, download, and commit it

on_version = MIN_VERSION
backoff = 5
while on_version <= MAX_VERSION:
    version_progress = f"{on_version}/{min(metadata_max_version, MAX_VERSION)}"
    print(f"Downloading version {version_progress}...")

    params = {
        "id": PLACE_ID,
        "version": on_version,
    }

    response = requests.get(
        f"https://assetdelivery.roblox.com/v1/asset",
        params,
        headers={
            "User-Agent": "Roblox/WinInet",
        },
        cookies=COOKIES,
        allow_redirects=True,
    )

    if response.status_code == 404:
        print("Got 404, ending download")
        break
    elif response.status_code != 200:
        print(
            f"Error {response.status_code} on {response.url} occurred while downloading, backing off:\n{response.text}"
        )
        time.sleep(backoff)
        backoff = backoff + BACKOFF_INCREMENT
        continue
    else:
        print(f"Saving version {version_progress}...")
        file_path = f"place_{PLACE_ID}.rbxl"
        with open(path.join(OUTPUT_DIRECTORY, file_path), "wb") as file:
            file.write(response.content)

        if LUNE_EXPAND_MODE:
            print(f"Running lune expand on version {version_progress}...")
            run_command(
                f'{lune} "{LUNE_EXPAND_PATH}" "{file_path}" {LUNE_EXPAND_MODE}',
                OUTPUT_DIRECTORY,
                None,
                error_on_failure=True,
            )

        print(f"Committing version {version_progress}...")
        metadata = version_metadata[on_version]

        if metadata == None:
            raise RuntimeError(
                f"Unable to get version metadata for version {version_progress}, aborting"
            )

        created = metadata["created"]
        is_published = metadata["isPublished"]

        if created == None or is_published == None:
            raise RuntimeError(
                f"Unable to use version metadata for version {version_progress}, aborting"
            )

        env = {
            "GIT_COMMITTER_DATE": created,
            "GIT_AUTHOR_DATE": created,
        }

        run_command(f"git add .", OUTPUT_DIRECTORY, env, error_on_failure=True)
        run_command(
            f'git commit -m "Version {on_version}"',
            OUTPUT_DIRECTORY,
            env,
            error_on_failure=True,
        )

        if is_published:
            print(f"Tagging version {version_progress}...")
            run_command(
                f'git tag -a "v{on_version}" -m "Published on {created} by {metadata["creatorType"]} {metadata["creatorTargetId"]}"',
                OUTPUT_DIRECTORY,
                env,
                error_on_failure=True,
            )

    on_version += 1
    backoff = BACKOFF_START

print("Done!")
