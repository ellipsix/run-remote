import shutil

def default_sanitizer(program, args):
    program = shutil.which(program) or program
    return (program, args) if program else None

class PathProgramWhitelist:
    def __init__(self, allowed_programs):
        self.allowed_programs = allowed_programs

    def __call__(self, program, args):
        if program in self.allowed_programs:
            program = shutil.which(program)
            return (program, args) if program else None
        else:
            return None
