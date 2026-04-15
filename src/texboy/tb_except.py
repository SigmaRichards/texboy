class TexboyError(Exception):
    pass

class TBFormatError(TexboyError):
    pass

class TBPathError(TexboyError):
    pass

class TBKeyError(TexboyError, KeyError):
    pass

class TBNoTarget(TexboyError):
    pass

class TBDependencyError(TexboyError):
    pass

class TBConfigError(TexboyError):
    pass

class TBUnknownError(TexboyError):
    pass
