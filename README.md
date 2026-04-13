This file is used to describe the file structure of this repository so that all repository contributors can build and utilize this repository in a consistent manner.

.gitignore - this is for listing out files/folders that are not shared with collaborators and not stored in Github (usually for security reasons and minimizing git repository size).

.env - a user stores passwords / API keys here. Not stored in git for security reasons.

/tmp - for a user to output data local data. Good for personal output files and/or testing new features. Not stored in git, since git is not to be used as a database of output data.

AGENTS.md - core agent entry point file

/skills - folder for skills files