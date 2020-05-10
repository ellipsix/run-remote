import shutil

def sanitize_command(program, args):
    if program in {'kwrite', 'kdiff3'}:
        program = shutil.which(program)
        return (program, args) if program else None
    elif program == 'bash' and len(args) == 1 and args[0] == 'test.sh':
        return ('/bin/bash', args)
    else:
        return None
