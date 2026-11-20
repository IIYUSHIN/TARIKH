# 0002 Delivery: GitHub and a final zip, worked on in Claude Code on the laptop

**Status:** Waiting for the repository name.

**Context:** The code has lived only on Claude's cloud machine, so Piyush could not see or run it. He uses Windows, has Claude
Code and VS Code installed, and has a GitHub account. A repository named TARIKH exists under the account IIYUSHIN, but Piyush
has not said that is the one, so Claude has not attached it.

**Decision:** Claude pushes to one GitHub repository that Piyush names, in small commits, on a branch called `rebuild`.
Piyush clones it on his laptop and opens it in Claude Code and VS Code. At the end Claude delivers a zip of everything.

**Why:** A repository gives Piyush the code, the history and every decision in one place, and lets him continue in Claude Code
without Claude's cloud machine.

**Cost if wrong:** If the repository cannot be attached, Claude sends zips instead, and Piyush unzips them on the laptop.

**Open item:** The repository named TARIKH is public. The project holds no secrets, but it carries Piyush's name and UID.
Piyush should decide whether it stays public or becomes private.
