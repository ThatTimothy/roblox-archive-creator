# roblox-archive-creator

Takes a Roblox Place and token, and creates a new git repo with each version as a dated commit.
Published versions are marked with a unique tag.

## Advanced Options

With advanced options enabled, you can:
- Output a .rbxlx along with the .rbxl
- Output all scripts to .luau files
  - For example, `game.Workspace.Script` -> `./scripts/Workspace/Script.luau`

# Download

Simply clone the repo:

```bash
git clone https://github.com/ThatTimothy/roblox-archive-creator.git
```

# Usage

> To use, first make sure you have **[Git](https://git-scm.com/downloads) and [Python 3.10](https://www.python.org/downloads/)** or greater installed. This may not work on lower versions.

First, install the required packages:

```bash
pip install -r requirements.txt
```

Then, run the code:

```
python main.py
```

Now, you'll be prompted for several options.
Answer them, and you'll be good to go!

## Advanced Options

You may notice when running you'll see something about advanced options being disabled. These aren't required, but provide [some options](#advanced-options).

To enable advanced options, follow the steps below.

> Note: Need [aftman](https://github.com/LPGhatguy/aftman) installed

```bash
aftman install
```

To verify it worked, run:
```bash
lune --version
```

You should see something like:
```
lune-cli x.y.z
```

<details>
<summary>Override lune path</summary>
To override lune location, use `ROBLOX_ARCHIVE_LUNE=lune-alternate` for example
</details>

<br>

When you run the above normal instructions again, you should now see the option to enable advanced options.

# FAQ

<details>
<summary>
I'm getting a not authorized error / 404 not found
</summary>
Make sure the cookie you provide is valid.
See if you can visit the site it failed to visit.
Make sure the versions provided exist.
</details>

# License

See [LICENSE.md](LICENSE.md)
