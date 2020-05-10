import asyncio
import logging
import shlex
import sys
from run_remote.command import sanitize_command

logger = logging.getLogger('run_remote.server')

async def copy_output(process, source_stream, destination_stream):
    while process.returncode is None:
        data = await source_stream.readline()
        if not data:
            if source_stream.at_eof():
                break
            else:
                continue
        destination_stream.write(b't ' + data)
        await destination_stream.drain()

async def run(program, *args, destination_stream=None):
    command = shlex.join([program] + list(args))
    logger.debug(f'Received request to run command: {command}')
    sanitized = sanitize_command(program, args)
    if not sanitized:
        destination_stream.write('q 126'.encode('ascii')) # 126 is the return code when running a non-executable program
        await destination_stream.drain()
        logger.warning(f'Command blocked by security policy: {command}')
        return
    logger.debug(f'Command accepted by security policy: {command}')
    program, args = sanitized
    command = shlex.join([program] + list(args))

    if destination_stream is None:
        destination = asyncio.subprocess.DEVNULL
    else:
        destination = asyncio.subprocess.PIPE
    logger.debug(f'About to run command {command}')
    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=destination,
        stderr=destination
    )
    logger.info(f'PID {process.pid} running command: {command}')
    io_tasks = []
    if destination_stream is not None:
        await asyncio.gather(
            copy_output(process, process.stdout, destination_stream),
            copy_output(process, process.stderr, destination_stream)
        )
        logger.debug(f'PID {process.pid} completed I/O')
    await process.wait()
    logger.info(f'PID {process.pid} exited with code {process.returncode}')
    destination_stream.write(f'q {process.returncode}'.encode('ascii'))
    await destination_stream.drain()

async def command_loop(reader, writer):
    try:
        data = await reader.readline()
        if not data or data[:2] != b'x ':
            addr = writer.get_extra_info('peername')
            logger.warning(f'Received unknown command from {addr!r}: {data.decode("ascii").rstrip()}')
            return
        program, *args = shlex.split(data[2:].decode('ascii').rstrip())
        await run(program, *args, destination_stream=writer)
    finally:
        writer.close()

async def serve(host, port):
    server = await asyncio.start_server(command_loop, host=host, port=port)
    logger.debug('Serving on ' + ','.join('{0}:{1}'.format(*s.getsockname()) for s in server.sockets))
    async with server:
        await server.serve_forever()
