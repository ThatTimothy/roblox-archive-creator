import math
import sys
from getpass import getpass
from os import path
from typing import Optional

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
                break

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
            break

        print(error_if_invalid)


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

# All configs are defined, start initial setup
