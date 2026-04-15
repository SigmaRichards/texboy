import os

from .logger import logWarn, logInfo
from . import tb_macro
from . import tb_config

DEFAULT_CONFIG = r"""
# Git directory should be defined in the root
#   but defaults to '.' if undefined
git_dir = '.'

# Values are propogated to all child tables
#   for the purposes of formatting
src_root   = "src"
build_root = "build"

[default]
# Default build_target tells texboy what to
#   build when none specified in texboy build
#   command
build_target = "main"

# Default build_dir will be used when one is
#   not specified in the targets build table.
#   Include the context variable "target"
build_dir = "{build_root}/{target}"

[macros]
# Where to save macro file for the purposes
#   of referring to versions, changes etc.
#   within the tex documents.
macro_file = "{src_root}/other/texboy.tex"

[diff]
# Where to place diff build targets
build_dir = "{build_root}/diff-{target}"

[build.main]
# The file which is used as the root for
#   the target
src = "{src_root}/main.tex"
"""

DEFAULT_DOCUMENT = r"""
\documentclass[a4paper]{article}

\input{src/other/texboy.tex}

\title{Hello, World!}
\author{Texboy Init}
\begin{document}
    \maketitle
    \begin{tabular}{rl}
        \textbf{Version}           & \tbversion \\
        \textbf{Tags}              & \tbtags \\
        \textbf{Diffs}             & \tbdiff \\
        \textbf{Untracked Changes} & \tbchanges \\
    \end{tabular}
\end{document}
"""

def writeDefaultConfig(path):
    if os.path.exists(path):
        logWarn(f"File already exists: {path}");
        return
    with open(path, 'w') as f:
        f.write(DEFAULT_CONFIG)

def writeDefaultDocument(path):
    if os.path.exists(path):
        logWarn(f"File already exists: {path}");
        return
    with open(path, 'w') as f:
        f.write(DEFAULT_DOCUMENT)

def initTexboy(root, no_dirs, no_main, no_config, no_macro):
    config_path = os.path.join(root, "texboy.toml")
    logInfo(f"Initializing texboy project in: {root}")
    if not no_dirs:
        os.makedirs(os.path.join(root, "src", "other"), exist_ok = True)
    if not no_main:
        writeDefaultDocument(os.path.join(root, "src", "main.tex"))
    if not no_config:
        writeDefaultConfig(config_path)
    if not no_macro:
        # Create macro file
        com_args = tb_config.CommandArguments(config_path)
        mac_args = com_args.getMacros()
        tb_macro.saveMacros(None, mac_args, None)
