# Texboy

*Texboy* is a command-line tool to assist in building Latex based projects. It started out as a simple Makefile, then a bash script, and now it's evolved into a python script.

This is the tool I've been using for quite some time to simplify a number of tasks I commonly need to do on latex documents. This often involves use of *other* tools to achieve this, but all streamlined into a single script.

 - Building: uses `latexmk` to build a project, and manages build directories and artifacts.
 - Latex macros so that the build can refer to version information in the document itself.
 - Calculating diff across version: combines `git` commands with `latexpand` and `latexdiff` to build diffs of the document across various versions.
 - Directory initialization: to quickly start a latex document
 - Basic dependency management: multiple build targets and dependency management to handle build order etc.

I've attempted to clean the code here and streamline the process but I'm sure there will be missing stuff. Let me know if you run into issues and hopefully I can fix them.

## Setup

In the future, this will likely be managed by pypi, but for now, its just this git repo. The tool is a python project managed by `uv`, so you'll want to ensure you have those setup (<https://docs.astral.sh/uv/>). Then clone the repo and `cd` into it.

To install the tool as is:
```
uv tool install .
```

To install the tool in editable mode:
```
uv tool install --editable .
```

The project also uses the following tools, which you will likely want to ensure are available. These are not *strictly* required, depending on what you want to do, but all of them are used by texboy for one thing or another.
 - `latexmk`: building latex documents with a single command
 - `latexpand`: expanding tex-files by following input/include commands.
 - `latexdiff`: diff highlighting between latex sources.
 - `git`: checking for changes, targetting specific versions for difference builds.

## Getting Started

The quickest way to get started is to create a new project. 

```
mkdir my_tex_project
cd my_tex_project
texboy init
```

The configuration file `texboy.toml` will give you a good starting point for configuring your project. You can also check `src/main.tex` for example usage of the provided macros. See below for more info on the `texboy init` command.

We can run `texboy build` to build the default target (`main` in this case), which should make a directory `build/main` and place artifacts in there, including `main.pdf`.

If we initialize the directory as a git repo, we can start building diffs.

```
git init

# Ignore build directory - not required but recommended
echo "build/*" >> .git/info/exclude

# Add in files to track
git add src/main.tex src/other/texboy.tex texboy.toml

# Commit
git commit -m "Texboy project initialized"
```

Then you can make some changes to `src/main.tex`. Once you've made some changes, you can run `texboy diff`, and it will create a version of `main` with the diffs highlighted, and place artifacts in `build/diff-main`.

## Configuration File

The texboy configuration file is just a `.toml` file. The simplest valid configuration which is able to build and create diffs is:

```
[build.main]
src = "src/main.tex"
build_dir = "build/main"
```

For any texboy command (excluding `init`), if `-c CONFIG` is specified, the `CONFIG` arg will be used as the configuration filepath to be loaded. Otherwise, texboy will first check `texboy.toml` in the current directory, then `.texboy.toml`.

This creates a single build target `main` and tells texboy where the root tex file is, and where to place build artifacts. This however, does not define a default target so every command which requires one will need to explicitly specify the target, nor does it create any macro file for use in your latex documents.

### Key Value Formatting

Apart from keys in tables which are used by the system directly, you are free to define any key in any table with any *string* value. The key itself can be *almost* any valid toml/python string. These keys get used as formatting variables for any subsequently defined strings, and will be in-scope for any strings in the same table (but defined AFTER the current one), and for all child tables. To format a string, you can use the python fstring syntax, i.e., surrounded by `{` and `}` like in `"value_{count}"`.

The simplest use case for this is defining global variables, which you can reuse throughout your configuration as formatting strings. However, it also allows you to re-write those variables in different contexts.

### Command Variables

Command variables are keys that texboy will *actually* lookup during normal operation. They can still be formatted, or be used for formatting following the rules above.

The following sections specify keys used in the various tables used by texboy.

#### Configuration Root
 - `git_dir`: Directory to use as git repo. Defaults to `"."` when unspecified.

#### Table `[default]`
 - `build_target`: The name of the target to use by default when unspecified. No default.
 - `build_dir`: The directory to use when building when target has unspecified. No default.

#### Table `[build.{target}]`
 - `.phony`: If this key is defined at all, then texboy won't run any commands to compile. It will still check for dependencies though. No default.
 - `src`: The root source file for the target to build. No default.
 - `build_dir`: The directory to place build artifacts in when building. No default, but will check `default.build_dir` if unspecified.
 - `job_name`: The job name to pass to latexmk when building. Defaults to `"{target}"`.
 - `groups`: List of names of groups this target is apart of. Used for determining dependencies. Defaults to `[]`.
 - `depends`: List of names of targets this target depends on. Defaults to `[]`.
 - `group-depends`: List of names of groups this target depends on. Defaults to `[]`.

#### Table `[diff]`
 - `build_dir`: The directory to place build artifacts in when building. No default, but will first check `build.target.build_dir`, then `default.build_dir` if unspecified.
 - `job_name`: The job name to pass to latexmk when building. Defaults to `"{target}_diffs"`.
 - `expand_src`: The file to save the output of latexpand to. When unspecified, will use a temporary file.
 - `expand_ref`: The file to save the output of latexpand to. When unspecified, will use a temporary file.
 - `diff_tex`: The file to save the output of latexdiff to. When unspecified, will use a temporary file.

#### Table `[default]`
 - `macro_file`: The file to save the latex macros to. When unspecified, will not save any file.
 - `macro_version`: The macro name for showing version number. Defaults to `"tbversion"`.
 - `macro_tags`: The macro name for showing version tags. Defaults to `"tbtags"`.
 - `macro_diff`: The macro name for showing the version the document has diffs calculated for. Defaults to `"tbdiff"`.
 - `macro_changes`: The macro name for showing if there's any untracked changes in the git repo. Defaults to `"tbchanges"`.

### Context Variables

Context variables are reserved names for keys which can be used for formatting, but the value is dependent on the context for which the command is being executed. Currently, the only context variable is `target`, however, there may be more in the future.

#### `target`

The context variable `target` is available for any build target table, in the diff table, or for `default.build_dir`. The value is the name for the build target currently being built. 

Consider the configuration:
```
[default]
target = "main"
build_dir = "build/default-{target}"

[build.main]
src = "src/main.tex"
jobname = "my-{target}"
build_dir = "build/main"
depends = [ "subdoc" ]

[build.subdoc]
src = "src2/main.tex"
jobname = "sub-{target}"
```

When we run `texboy build`, the default target `main` depends on `subdoc`, so that will be built first. `subdoc` will use default build-directory which becomes `build/default-subdoc`, with the jobname `sub-subdoc`. Then `main` will build in `build/main`, using jobname `my-main`.

### A Note About Scoping

Since command arguments are not reserved keys, and keys are scoped into child tables, if you define a command argument in a parent of the command's target table, it will still work. However, this results in some strange behaviour if you're not careful. E.g., If a `src` key is defined in the root, then all build targets will use that as their `src`, unless explicitly overwritten.

I believe the behaviour is well-defined provided you understand how the scoping works, so I haven't taken any steps to prevent this from happening.

However, the commands still require the tables to be defined, otherwise, the commands scope is undefined. For example, the following configuration will build with `texboy build`:

```
src = "src/main.tex"
build_dir = "build/main"
build_target = "main"
[default]
[build.main]
```

But this configuration will fail:
```
src = "src/main.tex"
build_dir = "build/main"
build_target = "main"
```

## Commands

### init

A project can be initialized with `texboy init`. The goal is to create a compiling project in a single command, so that you can quickly get to setting up the important parts. By default, it will do the following:
 1. Create the directories `src` and `src/other`
 2. Write the default tex document to `src/main.tex`
 3. Write the default config file to `texboy.toml`
 4. Write the default macro-file to `src/other/texboy.tex`

If any of the files exist when it tries to write, that step will be skipped.

There are the following additional options: 
  - `--no_dirs`: do not create the directories in step 1
  - `--no_main`: do not create the file in step 2
  - `--no_config`: do not create the config in step 3
  - `--no_macro`: do not create the macro file in step 4

## build

A build target can be built by using `texboy build [target]`. The `[target]` positional can be skipped if a default build target is defined in the configuration file, and it will build the default target.

If the target has dependencies (individual or group), it will check all dependencies can be built, before starting to build any. If it finds circular dependencies, it should fail before building any target.

Optionally, you can include the option `--skip_dependencies` and it will ignore checking and building the target's dependencies.

The build command for any target is equivalent to running:
```
latexmk {src} -outdir={build_dir} -jobname={job_name}
```

## diff

A diff build can be made by running `texboy diff [target] [--version ref_version]`. The `[target]` positional can be skipped if the deafult build target is defined in the configuration file, in which case it will build for the default target. The option `--version` is used to specify the version of the document to use as the version. This can either be a git hash or tag. If unspecified, it will use `HEAD`.

Dependency building is not currently implemented so the additional option `--skip_dependencies` is required.

The process is essential equivalent to the following steps (with some additional checks to handle some git issues for stash, detached head etc.):
```
# Current source file
latexpand {src} > {expand_src}

# Reference source file
git stash push
git checkout {version}
latexpand {src} > {expand_ref}
git stash pop

latexdiff {expand_ref} {expand_src} > {diff_tex}
latexmk {diff_tex} -outdir={build_dir} -jobname={job_name}
```
