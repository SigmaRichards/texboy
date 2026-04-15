#Copyright (c) 2023 Daniel Hess
#This code is licensed under the terms of the MIT license

"""
Basic logging class which allows for formatting and filtering.

Log types can be defined to log consistently. 
Verbosity levels can be specified to allow for certain logs to only "occasionally" print.
A set of log types can be specified for more fine-grained filtering.
Can specify the "print" function for output redirection.

Additionally, a wrapper class is supplied "BasicLogging" which allows for formatting of some basic types.
"""
import time
import re

class CODES:
    BOLD = 1
    UNDER = 4
    FAIL = 91
    OKGREEN = 92
    WARNING = 93
    OKBLUE = 94
    HEADER = 95
    OKCYAN = 96

class Logging:
    def __init__(self,parse_style = True, verbosity = 0, allowed_types = None, log_func = print):
        """
        If allowed_types is None
            Will print only log with verbosity >= self.verbosity
        else
            Will print only log with ltype in allowed_types
        """
        self._logf = log_func
        self.verbosity = verbosity
        self.allowed_logs = allowed_types
        self.parse_style = parse_style
        self.get_time = lambda : time.strftime("%d-%m-%y %I:%M:%S")
        if parse_style:
            self.style_par = re.compile(r"\/C(\d+)\[(.*?)\/C\1\]") #Matches anything between "/C1[" and "/C1]" as belonging to style #1
        self.styles = []
        self.end_sty = self._form_ccode()
        self.log_types = dict()
    def _form_ccode(self,*code):
        esc = '\033['
        codes = [str(a) for a in code]
        add = ';'.join(codes)
        if add == '':
            add = '0'
        ccode = fr'{esc}{add}m'
        return ccode
    def _style_text(self,style,text):
        if style >= len(self.styles):
            return text
        sty_args = self.styles[style]
        sty_code = self._form_ccode(*sty_args)
        out = f"{sty_code}{text}{self.end_sty}"
        return out
    def _parse_text(self,text,parse = None):
        po = self.parse_style if parse is None else parse
        out = text
        if not po:
            return out
        while (sval := self.style_par.search(out)) is not None:
            lit, grp, ctext = sval.group(0,1,2)
            new_text = self._style_text(int(grp),ctext)
            out = out.replace(lit,new_text)
        return out
    def set_log_type(self,log_type,prefix,suffix,parse = None):
        pre,suf = [self._parse_text(a,parse = parse) for a in [prefix,suffix]]
        self.log_types[log_type] = [pre,suf]
        return
    def log(self,*args,ltype = None, v = 0):
        if self.allowed_logs is None:
            if v < self.verbosity:
                return
        else:
            if ltype not in self.allowed_logs:
                return
        gt = self.get_time()
        print_args = [self._parse_text(a) if type(a) is str else a for a in args]
        if ltype is not None:
            pre, suf = [[a] if a is not None else [] for a in self.log_types[ltype]]
            print_args = [*pre,*print_args,*suf]
        self._logf(gt,*print_args)
        return

class BasicLogging(Logging):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append([CODES.OKGREEN,CODES.UNDER])
        self.styles.append([CODES.WARNING])
        self.styles.append([CODES.FAIL,CODES.BOLD])
        self.styles.append([CODES.OKCYAN])
        self.set_log_type('okay',"/C0[(OKAY)/C0]","")
        self.set_log_type('warn',"/C1[(WARN)/C1]","")
        self.set_log_type('fail',"/C2[(FAIL)/C2]","")
        self.set_log_type('info',"/C3[(INFO)/C3]","")
        return

LOGGER = BasicLogging(verbosity = 1)

# Convenience functions
def logOkay(*args, v = 2, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'okay', v = v)

def logInfo(*args, v = 1, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'info', v = v)

def logWarn(*args, v = 2, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'warn', v = v)

def logFail(*args, v = 3, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'fail', v = v)

# Convenience decorators
def loggedFail(fail_msg):
    def _loggedFailInner(f):
        def _loggedFailInnerInner(*args, **kwargs):
            try:
                ret = f(*args, **kwargs)
            except BaseException as e:
                logFail(fail_msg)
                logInfo(f" - Failure caused by: {type(e)}")
                raise e
            return ret
        return _loggedFailInnerInner
    return _loggedFailInner


# Verbose variants to rarely print
def logVOkay(*args, v = 0, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'okay', v = v)

def logVInfo(*args, v = 0, **kwargs):
    LOGGER.log(*args, **kwargs, ltype = 'info', v = v)

