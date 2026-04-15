from git import Repo

class GitRepo:
    def __init__(self, git_dir):
        self.git_dir = git_dir

    def getRepo(self):
        repo = None
        try:
            repo = Repo(self.git_dir)
        except:
            pass
        return repo
    
    def getCurrentVersion(self):
        repo = self.getRepo()
        if repo is None:
            return None, None
        hexstr = repo.rev_parse('HEAD').hexsha
        tags = repo.git.tag('--points-at', 'HEAD')
        tags = tags.split('\n')
        return hexstr, tags

    def hasUntrackedChanges(self):
        repo = self.getRepo()
        if repo is None:
            return None
        return len(repo.git.status('--porcelain')) > 0

    def operateRepoAt(self, target_ref = None):
        repo = self.getRepo()
        if repo is None:
            raise RuntimeError("Cannot load git directory")
        return OperateRepoAt(repo, target_ref = target_ref)

class OperateRepoAt:
    """
    Context manager to allow us to move through the git-repo without affecting changes
    """
    def __init__(self, repo, target_ref = None):
        self.repo = repo
        self.target_ref = target_ref
        self.restore_ref = repo.git.branch('--show-current')
        if self.restore_ref == '':
            # in detached head
            self.restore_ref = repo.rev_parse('HEAD')
        self._stashed = False

    def __enter__(self):
        ret = val = self.repo.git.stash('push')
        if ret != "No local changes to save":
            self._stashed = True
        if self.target_ref is not None:
            self.repo.git.checkout(self.target_ref)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.target_ref is not None:
            self.repo.git.checkout(self.restore_ref)
        if self._stashed:
            self.repo.git.stash('pop')
            self._stashed = False
        return
