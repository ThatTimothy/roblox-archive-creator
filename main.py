import json
import math
import os
import subprocess
import sys
from getpass import getpass
from os import path
from typing import Optional, Tuple

import requests

# Optional values to configure
DEFAULT_OUTPUT_DIRECTORY = "output/"
COOKIE_CACHE_PATH = "cookie.txt"
PROMPT_FOR_COOKIE_CACHE = True

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


# Git utils
def run_command(command: str, cwd=".", env=None) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to run `{command}`:\n{result.stderr}")

    return result.stdout


# Validate git exists
run_command("git --version")

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

# Print out all configs
print(
    f"\nFinal configuration:\n"
    + f"  Output directory: {OUTPUT_DIRECTORY}\n"
    + f"  Roblox cookie: ***\n"
    + f"  Place Id: {PLACE_ID}\n"
    + f"  Minimum version: {MIN_VERSION}\n"
    + f"  Maximum version: {MAX_VERSION if MAX_VERSION != sys.maxsize else 'none'}\n"
)

# All configs are defined, start initial setup

print("Creating directory...")
os.makedirs(OUTPUT_DIRECTORY)
run_command("git init", OUTPUT_DIRECTORY)

COOKIES = {
    ".ROBLOSECURITY": ROBLOX_COOKIE,
}

# Get version metadata
version_metadata = {}

cursor = None
page = 1
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
        version_metadata[metadata["assetVersionNumber"]] = metadata

    cursor = json_response["nextPageCursor"]

    if not cursor:
        break

    page += 1

# Go through each version, download, and commit it

on_version = MIN_VERSION
while on_version <= MAX_VERSION:
    print(f"Downloading version {on_version}...")

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

    if response.status_code == 400:
        print("Got 404, ending download")
        break
    elif response.status_code != 200:
        raise RuntimeError(
            f"Error {response.status_code} on {response.url} occurred while downloading, aborting:\n{response.text}"
        )
    else:
        print(f"Saving version {on_version}...")
        with open(path.join(OUTPUT_DIRECTORY, f"place_{PLACE_ID}.rbxl"), "wb") as file:
            file.write(response.content)

        print(f"Committing version {on_version}...")
        metadata = version_metadata[on_version]

        if metadata == None:
            raise RuntimeError(
                f"Unable to get version metadata for version {on_version}, aborting"
            )

        created = metadata["created"]
        is_published = metadata["isPublished"]

        if created == None or is_published == None:
            raise RuntimeError(
                f"Unable to use version metadata for version {on_version}, aborting"
            )

        env = {
            "GIT_COMMITTER_DATE": created,
        }

        run_command(f"git add .", OUTPUT_DIRECTORY, env)
        run_command(
            f'git commit -m "Version {on_version}"',
            OUTPUT_DIRECTORY,
            env,
        )

        if is_published:
            run_command(
                f'git tag -a "v{on_version}" -m "Published on {created} by {metadata["creatorType"]} {metadata["creatorTargetId"]}"',
                OUTPUT_DIRECTORY,
                env,
            )

    on_version += 1

print("Done!")
