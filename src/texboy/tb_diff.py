import subprocess
import tempfile

#import TBMacro
#from TBBuild import buildTex
#from TBGit import GitRepo
from . import tb_config
from . import tb_build
from . import tb_macro

from .logger import logInfo

def diff(config_path, target, ref_version, skip_deps):
    # Get build information
    com_args    = tb_config.CommandArguments(config_path)
    git_repo = com_args.getRepo()
    pre_build, final_build = com_args.getDiffBuildList(target, build_deps = not skip_deps)
    # Save macro
    c_diff = ref_version if ref_version is not None else "calculated from HEAD"
    mac_args = com_args.getMacros()
    tb_macro.saveMacros(c_diff, mac_args, git_repo)
    # Pre build
    if len(pre_build) > 0:
        raise NotImplementedError("Diff dependency building not implemented yet!")
    if final_build[1]['.phony'] is None:
        raise NotImplementedError("Cannot build diff for .phony target")
    # Run diff build
    buildDiff(
        final_build[1]['src'],
        final_build[1]['expand_src'],
        final_build[1]['expand_ref'],
        final_build[1]['diff_tex'],
        final_build[1]['build_dir'],
        final_build[1]['job_name'],
        git_repo,
        ref_version
    )
    # Reset macro file
    tb_macro.saveMacros(None, mac_args, None)

    # 1. Create Macro
    # 2. Build everything at current git state
    # 3. Get target.src and expand into expand_src
    # 4. Move git to ref_version
    # 5. Build everything *again*
    # 6. Get target.src and expand into expand_ref
    # 7. Create diff_tex from expand_src and expand_ref
    # 8. Compile target with diff_tex as src

def expandTex(src, dst):
    with open(dst, 'w') as f:
        subprocess.run(['latexpand', src], stdout = f)

def diffTex(src_a, src_b, dst):
    with open(dst, 'w') as f:
        subprocess.run(['latexdiff', src_a, src_b], stdout = f)

class CMFilepath:
    def __init__(self, path):
        """
        If path is not None, the file at `path' will persist,
          otherwise will make the file temporary.

        Will manage files inside context manager.
        """
        self.path = path
        self._ntf = None

    def __enter__(self):
        if self.path is None:
            self._ntf = tempfile.NamedTemporaryFile()
            return self._ntf.name
        return self.path

    def __exit__(self, *args, **kwargs):
        if self._ntf is not None:
            _ = self._ntf.__enter__()
            return self._ntf.__exit__(*args, **kwargs)
        return

class CMMultiFile:
    """
    Manages multiple CMFilepath context managers simultaneously
    """
    def __init__(self, *paths):
        self.cms = [CMFilepath(p) for p in paths]
    def __enter__(self):
        paths = [f.__enter__() for f in self.cms]
        return paths
    def __exit__(self, *args, **kwargs):
        out = [f.__exit__(*args, **kwargs) for f in self.cms]
        return out[-1]

def buildDiff(
        file,
        tmp_a,
        tmp_b,
        tmp_c,
        build_dir,
        job_name,
        git_repo,
        target_ref
    ):
    with CMMultiFile(tmp_a, tmp_b, tmp_c) as tmp_files:
        tf_a, tf_b, tf_c = tmp_files
        logInfo(f"Created files: {tf_a}, {tf_b}, {tf_c}")
        expandTex(file, tf_a)
        with git_repo.operateRepoAt(target_ref = target_ref):
            expandTex(file, tf_b)
        diffTex(tf_b, tf_a, tf_c)
        tb_build.buildTex(tf_c, build_dir, job_name)
    return
