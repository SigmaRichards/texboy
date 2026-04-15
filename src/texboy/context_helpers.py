from .logger import logWarn
from .tb_except import *

# Uses flattened dict format to distinguish
#   tables from values
CONTEXT_VARIABLES = {
    # All values in target can use "target"
    ("build",): [ "target" ],
    # Some variables in diff can use target
    ("diff", "build_dir"):  [ "target" ],
    ("diff", "job_name"):   [ "target" ],
    ("diff", "expand_src"): [ "target" ],
    ("diff", "expand_ref"): [ "target" ],
    ("diff", "diff_tex"):   [ "target" ],
    # Default build_dir can use target
    ("default", "build_dir"): [ "target" ],
}
COMMAND_VARIABLES = {
    "git_dir": ".",
    "default": {
        "build_target":    None,
        "build_dir": None,
    },
    "build": {
        "src":           None,
        "build_dir":     None,
        "job_name":      "{target}",
        "groups":        [],
        "depends":       [],
        "group-depends": [],
    },
    "diff": {
        "build_dir":       None,
        "job_name":        "{target}_diffs",
        "expand_src":      None,
        "expand_ref":      None,
        "diff_tex":        None,
        "include_targets": None,
        "exclude_targets": None,
        "include_groups":  None,
        "exclude_groups":  None,
    },
    "macros": {
        "macro_file":    None,
        "macro_version": "tbversion",
        "macro_tag":     "tbtags",
        "macro_diff":    "tbdiff",
        "macro_changes": "tbchanges",
    }
}

# Classes to simplify comparisons
class FlatKey:
    def __init__(self, key):
        self.key = key

    def isEqual(self, other):
        if len(other.key) != len(self.key):
            return False
        for lk, rk in zip(other.key, self.key):
            if lk != rk:
                return False
        return True

    def isChild(self, other):
        """
        Is `other' child of `self'
        """
        if len(other.key) <= len(self.key):
            return False
        for lk, rk in zip(other.key, self.key):
            if lk != rk:
                return False
        return True

    def isImmediateChild(self, other):
        """
        Is `other' child of `self'
        """
        if len(self.key) + 1 != len(other.key):
            return False
        return self.isChild(other)

    def isParent(self, other):
        """
        Is `other' parent of `self'
        """
        return other.isChild(self)

    def isImmediateParent(self, other):
        """
        Is `other' parent of `self'
        """
        return other.isImmediateChild(self)

class ContextVariable:
    def __init__(self, context_key, vars = {}):
        self.key  = FlatKey(context_key)
        self.vars = vars

    def isInContext(self, key):
        fk = FlatKey(key)
        return self.key.isChild(fk) or self.key.isEqual(fk)

    def getPlaceholders(self):
        return {k:f"{{{k}}}" for k in self.vars}

# Convert between dict formats
def flattenDictTree(d):
    out = {}
    for k,v in d.items():
        if type(v) is dict:
            for (ik, iv) in flattenDictTree(v).items():
                new_k = (k,) + ik
                out[new_k] = iv
        else:
            out[(k,)] = v
    return out

def inflateDict(d):
    def _insert(d, v, k, *ks):
        if len(ks) == 0:
            d[k] = v
            return d
        if k not in d:
            d[k] = {}
        d[k] = _insert(d[k], v, *ks)
        return d
    out = {}
    for ks, v in d.items():
        _insert(out, v, *ks)
    return out

def isContextVariable(var_name):
    all_context_vars = [v for vs in CONTEXT_VARIABLES.values() for v in vs]
    return var_name in all_context_vars

def getContextVars(key):
    all_vars = []
    for c_context, c_vars in CONTEXT_VARIABLES.items():
        if ContextVariable(c_context, c_vars).isInContext(key):
            all_vars.extend(c_vars)
    return {k:f"{{{k}}}" for k in set(all_vars)}

def strictFormat(key, s, use_vars):
    class DDefault(dict):
        def __missing__(self, c_key):
            err = f"Key `{key}' requires formatting variable `{c_key}' which doesn't exist in this context."
            raise TBFormatError(err)
    return s.format_map(DDefault(**use_vars))

def contextFormat(key, s, avail_vars):
    use_vars = avail_vars.copy()
    use_vars.update(getContextVars(key))
    return strictFormat(key, s, use_vars)

def propogateFormatting(var_dict):
    def _propogateFormatting(avail_vars, c_dict, *context):
        new_vars     = {k:v for k,v in avail_vars.items()}
        context_vars = getContextVars(context)
        # Process all values
        for k, v in c_dict.items():
            if type(v) is dict:
                continue
            full_key = context + (k,)
            if isContextVariable(k):
                logWarn(f"Key `{full_key}` uses reserved variable name, ignoring.")
                continue
            if type(v) is list:
                new_val = [contextFormat(full_key, inner_v, new_vars) for inner_v in v]
            else:
                new_val = contextFormat(full_key, v, new_vars)
            new_vars[k] = new_val
        # Process all dicts
        for k, v in c_dict.items():
            if type(v) is not dict:
                continue
            new_context = context + (k,)
            new_vars[k] = _propogateFormatting(new_vars, v, *new_context)
        return new_vars
    return _propogateFormatting({}, var_dict)
