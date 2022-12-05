import shutil
from typing import Callable, Container, Iterable, Optional, Tuple

Command = str
Arguments = Iterable[str]


def default_sanitizer(program: Command, args: Arguments) -> Optional[Tuple[Command, Arguments]]:
    program = shutil.which(program) or program
    return (program, args) if program else None


class PathProgramWhitelist:
    def __init__(self, allowed_programs: Container[Command]) -> None:
        self.allowed_programs = allowed_programs

    def __call__(self, program: Command, args: Arguments):
        if program in self.allowed_programs:
            qualified_program: Optional[str] = shutil.which(program)
            return (qualified_program, args) if qualified_program else None
        else:
            return None


CommandSanitizer = Callable[[Command, Arguments], Optional[Tuple[Command, Arguments]]]
