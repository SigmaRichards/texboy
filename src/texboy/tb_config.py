import os
import toml

from . import context_helpers as H
from .tb_except import *
from .logger import logOkay, logInfo, logWarn, logFail, logVInfo, logVOkay, loggedFail
from . import tb_git

CONFIG_FILE_RESOLUTION = [
    "texboy.toml",
    ".texboy.toml",
]

COMMAND_VARIABLES = {
    "git_dir": ".",
    "default": {
        "build_target": None,
        "build_dir":    None,
    },
    "build": {
        "src":           None,
        "build_dir":     None,
        "job_name":      "{target}",
        "groups":        [],
        "depends":       [],
        "group-depends": [],
        ".phony":        None
    },
    "diff": {
        "build_dir":       None,
        "job_name":        "{target}_diffs",
        "expand_src":      None,
        "expand_ref":      None,
        "diff_tex":        None,
    },
    "macros": {
        "macro_file":    None,
        "macro_version": "tbversion",
        "macro_tags":    "tbtags",
        "macro_diff":    "tbdiff",
        "macro_changes": "tbchanges",
    }
}

# Object to use to fail properly when getting values without defaults
#   so that None is allowed
_NO_DEFAULT = object()

class Config:
    def __init__(self, path, lazy = True, lazy_format = True):
        self.config_path = path
        self._raw_dict  = None
        self._formatted = None
        self._lazy_format = lazy_format
        if (not lazy) or (not lazy_format):
            self.reloadDict()

    def reloadDict(self):
        if self._raw_dict is not None:
            logWarn(f"Force reloading config")
        # Resolve path
        if self.config_path is None:
            logVInfo("No config path explicitly set, resolving.")
            for c_path in CONFIG_FILE_RESOLUTION:
                if os.path.isfile(c_path):
                    self.config_path = c_path
                    break
            else:
                raise TBPathError(f"Could not find valid texboy config file")
        # Check path valid
        logVInfo(f"Using config file: {self.config_path}")
        if not os.path.isfile(self.config_path):
            raise TBPathError(f"Config is not file: {self.config_path}")
        # Load the file
        with open(self.config_path, 'r') as f:
            self._raw_dict = toml.load(f)
        logVOkay(f"Config file loaded")
        self._formatted = None
        if not self._lazy_format:
            self.reloadFormatted()
        return

    def getDict(self, flat = True):
        if self._raw_dict is None:
            self.reloadDict()
        out = self._raw_dict.copy()
        if flat:
            out = H.flattenDictTree(out)
        return out

    def reloadFormatted(self):
        if self._formatted is not None:
            logWarn(f"Force re-formatting config")
        config_dict = self.getDict(flat = False)
        self._formatted = H.propogateFormatting(config_dict)
        return 

    def getFormatted(self, flat = True):
        if self._formatted is None:
            self.reloadFormatted()
        out = self._formatted.copy()
        if flat:
            out = H.flattenDictTree(out)
        return out

    def getValue(self, *key, default = _NO_DEFAULT):
        f_config = self.getFormatted(flat = True)
        val = f_config.get(key, default)
        if val is _NO_DEFAULT:
            raise TBKeyError(f"Could not get key from config and no default: `{key}'")
        return val

class CommandArguments:
    def __init__(self, path, lazy = True, lazy_format = True):
        self.config = Config(path, lazy = lazy, lazy_format = lazy_format)
        # Get all build targets
        self.all_targets = []
        build_table = self.config.getFormatted(flat = False).get("build", {})
        for k, v in build_table.items():
            if type(v) is dict:
                self.all_targets.append(k)
        # Targets by group
        self.target_groups = {}
        for target in self.all_targets:
            for c_group in self.config.getValue("build", target, "groups", default = []):
                if c_group not in self.target_groups:
                    self.target_groups[c_group] = []
                self.target_groups[c_group].append(target)
        self._repo = None

    def getRepo(self):
        if self._repo is None:
            self._repo = tb_git.GitRepo(
                self.config.getValue("git_dir", default = COMMAND_VARIABLES['git_dir'])
            )
        return self._repo

    def targetCanCompile(self, target):
        phony = self.config.getValue("build", target, ".phony", default = None)
        if phony is not None:
            return True
        src = self.config.getValue("build", target, "src", default = None)
        return (src is not None)

    def resolveTarget(self, target, allow_default_target = False):
        if allow_default_target:
            if target is None:
                # Get default
                target = self.config.getValue("default", "build_target", default = None)
        if target is None:
            raise TBNoTarget("No target specified and no default configured.")
        # Ensure target exists
        if not self.targetCanCompile(target):
            raise TBNoTarget(f"Target cannot be compiled: {target}")
        return target

    def getSingleBuildArgs(self, target, allow_default_target = False):
        target = self.resolveTarget(target, allow_default_target)
        out = {}
        for k, default in COMMAND_VARIABLES["build"].items():
            out[k] = self.config.getValue("build", target, k, default = default)
        if out['.phony'] is None:
            if out['src'] is None:
                raise TBConfigError(f"Target `{target}' does not have `src'")
            if out['build_dir'] is None:
                out['build_dir'] = self.config.getValue("default", "build_dir", default = None)
                if out['build_dir'] is None:
                    raise TBConfigError(f"Target `{target}' does not have `build_dir' and no default defined.")
        for k,v in out.items(): 
            try:
                if v is None:
                    continue
                if type(v) is list:
                    out[k] = [H.strictFormat(k, inner_v, {"target": target}) for inner_v in v] 
                    continue
                out[k] = H.strictFormat(k, v, {"target": target})
            except TBFormatError:
                raise TBUnknownError(f"Build not exposing promised variables! Key: {k}")
        return (target, out)

    def getBuildList(self, target, build_deps = True):
        root, root_config = self.getSingleBuildArgs(target, True)
        if not build_deps: 
            return [(root, root_config)]
        build_configs = {}
        build_order   = []
        groups_built  = []
        seen_group    = []
        def _addDepGroup(c_group):
            if c_group in groups_built:
                return None
            if c_group in seen_group:
                return [ (c_group,) ]
            seen_group.append(c_group)
            for d in self.target_groups[c_group]:
                ret = _addDeps(d)
                if ret is not None:
                    return [(c_group, ret)]
            groups_built.append(c_group)
            return None
        def _addDeps(c_target, c_config = None):
            if c_target in build_order:
                return None
            if c_target in build_configs:
                return [c_target]
            if c_config is None:
                _, c_config = self.getSingleBuildArgs(c_target)
            build_configs[c_target] = c_config
            # Resolve named dependencies
            for d in c_config['depends']:
                ret = _addDeps(d)
                if ret is not None:
                    return [c_target] + ret
            # Resolve groups of dependencies
            for g in c_config['group-depends']:
                ret = _addDepGroup(g)
                if ret is not None:
                    return [c_target] + ret
            build_order.append(c_target)
            return None
        ret = _addDeps(root, root_config)
        if ret is not None:
            raise TBDependencyError(f"Circular dependency found: {ret}")
        out = [
            (k, build_configs[k]) for k in build_order
        ]
        return out
    def getMacros(self):
        out = {}
        for k, default in COMMAND_VARIABLES["macros"].items():
            out[k] = self.config.getValue("macros", k, default = default)
        return out

    def getDiffBuildList(self, target, build_deps = True):
        *pre_build, final_build = self.getBuildList(target, build_deps = build_deps)
        c_target = final_build[0]
        new_build = final_build[1].copy()
        for k, default in COMMAND_VARIABLES["diff"].items():
            new_val = self.config.getValue("diff", k, default = default)
            if new_val is None:
                new_val = new_build.get(k, new_val)
            elif type(new_val) is list:
                new_val = [H.strictFormat(k, inner_v, {"target": c_target}) for inner_v in new_val] 
            else:
                new_val = H.strictFormat(k, new_val, {"target": c_target})
            new_build[k] = new_val
        return pre_build, (c_target, new_build)
