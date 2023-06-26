# roblox-archive-creator

Takes a Roblox Place and token, and creates a new git repo with each version as a dated commit.
Published versions are marked with a unique tag.

# Download

Simply clone the repo:

```bash
git clone https://github.com/ThatTimothy/roblox-archive-creator.git
```

# Usage

> To use, first make sure you have **Git and Python 3.10** or greater installed. This may not work on lower versions.

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
