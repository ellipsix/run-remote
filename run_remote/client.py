import asyncio
import logging
import shlex
import sys
from run_remote.command import Arguments, Command
from typing import List, Optional


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.logger = logging.getLogger("run_remote.client")
        self.host = host
        self.port = port

    async def read_commands(self, source_stream) -> Optional[int]:
        while True:
            data = await source_stream.readline()
            if not data:
                if source_stream.at_eof():
                    break
                else:
                    continue
            if data[:2] == b"t ":
                print(data[2:].decode("ascii").rstrip())
            elif data[:2] == b"q ":
                return int(data[2:].decode("ascii"))
        return None

    async def run(self, program: Command, *args) -> Optional[int]:
        command = shlex.join([program] + list(args))
        self.logger.info(f"[{program}] <starting>")
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(f"x {command}\n".encode("ascii"))
        await writer.drain()
        exit_code: Optional[int] = await self.read_commands(reader)
        writer.close()
        if exit_code is not None:
            self.logger.info(f"[{program}] <exited with code {exit_code}>")
        else:
            self.logger.error(f"[{program}] <exited with unknown code>")
        return exit_code
