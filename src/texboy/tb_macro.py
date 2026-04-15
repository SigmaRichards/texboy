from . import tb_config

def saveMacros(diff, args, repo):
    if args["macro_file"] is None:
        return
    if repo is None:
        c_version = "Uninitialized texboy macro"
        c_tags    = "Uninitialized texboy macro"
        c_changes = "Uninitialized texboy macro"
        c_diff    = "Uninitialized texboy macro"
    else:
        c_version, c_tags = repo.getCurrentVersion()
        c_changes = "repo has untracked changes" if repo.hasUntrackedChanges() else "none"
        c_diff = "no diff calculated" if diff is None else diff
    macros = [
        createMacro(args["macro_version"], c_version),
        createMacro(args["macro_tags"],    c_tags),
        createMacro(args["macro_diff"],    c_diff),
        createMacro(args["macro_changes"], c_changes),
    ]
    macro_full = '\n'.join(macros)
    with open(args["macro_file"], 'w') as f:
        f.write(macro_full)

def createMacro(name, value):
    command = f"\\newcommand{{\\{name}}}{{{value}}}"
    return command
