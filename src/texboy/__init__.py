import argparse

from . import tb_init
from . import tb_build
from . import tb_diff

from . import logger
from .logger import logVInfo, logVOkay, logInfo, logOkay, logWarn, logFail, loggedFail

# Parent type for defining sub-commands
class SubCommand:
    def __init__(self, subparser):
        raise NotImplemented
    def run(self, args):
        raise NotImplemented

class BuildCmd(SubCommand):
    def __init__(self, subparser):
        subparser.add_argument('target', default = None, nargs = "?")
        subparser.add_argument('--skip_dependencies', action='store_true')
    def run(self, args):
        tb_build.build(args.config, args.target, args.skip_dependencies)

class InitCmd(SubCommand):
    def __init__(self, subparser):
        #subparser.add_argument('-d', '--directory', default = ".")
        subparser.add_argument('--no_dirs',   action = "store_true")
        subparser.add_argument('--no_main',   action = "store_true")
        subparser.add_argument('--no_config', action = "store_true")
        subparser.add_argument('--no_macro',  action = "store_true")
    def run(self, args):
        tb_init.initTexboy(
            ".",
            args.no_dirs,
            args.no_main,
            args.no_config,
            args.no_macro
        )

class DiffCmd(SubCommand):
    def __init__(self, subparser):
        subparser.add_argument('target', default = None, nargs = "?")
        subparser.add_argument('-V', '--version', default = None)
        subparser.add_argument('--skip_dependencies', action='store_true')
    def run(self, args):
        logInfo("Diff command")
        tb_diff.diff(args.config, args.target, args.version, args.skip_dependencies)

def createSubCommand(name, subparsers, sub_cmd):
    """
    Helper function for creating sub-command parsers.
    Ensures that the child-type handles itself.
    """
    subparser = subparsers.add_parser(name)
    sub_cmd   = sub_cmd(subparser)
    subparser.set_defaults(
        func = loggedFail(f"Failed to run command: {name}")(sub_cmd.run)
    )
    return sub_cmd

def getArgs():
    @loggedFail("Failed to create parser")
    def _create():
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config',  default = None)
        parser.add_argument('-v', '--verbose', action = 'store_true')
        parser.add_argument('-q', '--quiet', action = 'store_true')
        # Subparsers
        subparsers = parser.add_subparsers(required=True)
        createSubCommand('init',         subparsers, InitCmd)
        createSubCommand('build',        subparsers, BuildCmd)
        createSubCommand('diff',         subparsers, DiffCmd)
        #createSubCommand('compress',     subparsers,)
        #createSubCommand('dependencies', subparsers,)
        return parser
    @loggedFail("Failed to parse arguments")
    def _parse(parser):
        return parser.parse_args()
    # Run
    return _parse(_create())

def main() -> None:
    # Primary parser
    args = getArgs()
    if args.verbose:
        logger.LOGGER.verbosity = 0 
    if args.quiet:
        logger.LOGGER.verbosity = 100 
    logVInfo("Arguments parsed")
    args.func(args)
