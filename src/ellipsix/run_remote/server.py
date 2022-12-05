import asyncio
import logging
import shlex
import sys
from ellipsix.run_remote.command import Arguments, Command, CommandSanitizer
from typing import List


class Server:
    def __init__(self, host: str, port: int, command_sanitizer: CommandSanitizer) -> None:
        self.logger = logging.getLogger("ellipsix.run_remote.server")
        self.host = host
        self.port = port
        self.sanitizer = command_sanitizer

    async def copy_output(self, process, source_stream, destination_stream) -> None:
        while process.returncode is None:
            data = await source_stream.readline()
            if not data:
                if source_stream.at_eof():
                    break
                else:
                    continue
            destination_stream.write(b"t " + data)
            await destination_stream.drain()

    async def run(self, program: Command, *args: str, destination_stream=None) -> None:
        command = shlex.join([program] + list(args))
        self.logger.debug(f"Received request to run command: {command}")
        sanitized = self.sanitizer(program, args)
        if not sanitized:
            destination_stream.write(
                "q 126".encode("ascii")
            )  # 126 is the return code when running a non-executable program
            await destination_stream.drain()
            self.logger.warning(f"Command blocked by security policy: {command}")
            return
        self.logger.debug(f"Command accepted by security policy: {command}")
        command = shlex.join([sanitized[0]] + list(sanitized[1]))

        if destination_stream is None:
            destination = asyncio.subprocess.DEVNULL
        else:
            destination = asyncio.subprocess.PIPE
        self.logger.debug(f"About to run command {command}")
        process = await asyncio.create_subprocess_exec(program, *args, stdout=destination, stderr=destination)
        self.logger.info(f"PID {process.pid} running command: {command}")
        if destination_stream is not None:
            await asyncio.gather(
                self.copy_output(process, process.stdout, destination_stream),
                self.copy_output(process, process.stderr, destination_stream),
            )
            self.logger.debug(f"PID {process.pid} completed I/O")
        await process.wait()
        self.logger.info(f"PID {process.pid} exited with code {process.returncode}")
        destination_stream.write(f"q {process.returncode}".encode("ascii"))
        await destination_stream.drain()

    async def command_loop(self, reader, writer) -> None:
        try:
            data = await reader.readline()
            if not data or data[:2] != b"x ":
                addr = writer.get_extra_info("peername")
                self.logger.warning(f'Received unknown command from {addr!r}: {data.decode("ascii").rstrip()}')
                return
            program, *args = shlex.split(data[2:].decode("ascii").rstrip())
            await self.run(program, *args, destination_stream=writer)
        finally:
            writer.close()

    async def serve(self) -> None:
        server = await asyncio.start_server(self.command_loop, host=self.host, port=self.port)
        if not server.sockets:
            raise RuntimeError(f"Unable to initialize server on {self.host}:{self.port}")
        self.logger.debug("Serving on " + ",".join("{0}:{1}".format(*s.getsockname()) for s in server.sockets))
        async with server:
            await server.serve_forever()
