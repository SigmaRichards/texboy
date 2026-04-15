#!/usr/bin/env python3

import subprocess

from . import tb_macro
from . import tb_config
from .logger import logInfo

def build(config_path, target, skip_deps):
    com_args = tb_config.CommandArguments(config_path)
    mac_args = com_args.getMacros()
    tb_macro.saveMacros(None, mac_args, com_args.getRepo())
    build_order = com_args.getBuildList(target, build_deps = not skip_deps)
    for (c_target, c_args) in build_order:
        logInfo(f"Building: {c_target}")
        if c_args['.phony'] is None:
            buildTex(
                file      = c_args['src'],
                build_dir = c_args['build_dir'],
                job_name  = c_args['job_name'],
            )
        else:
            logInfo(f".phony target")
    # Once built, de-init macro file
    tb_macro.saveMacros(None, mac_args, None)
    return

def buildTex(file, build_dir, job_name):
    args = ["latexmk"]
    if file is not None:
        args.append(file)
    if build_dir is not None:
        args.append(f"-outdir={build_dir}")
    if job_name is not None:
        args.append(f"-jobname={job_name}")
    subprocess.run(args)
