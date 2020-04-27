import asyncio
import logging
import shlex
import sys

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
    if destination_stream is None:
        destination = asyncio.subprocess.DEVNULL
    else:
        destination = asyncio.subprocess.PIPE
    logger.info(f'[{program}] <starting>')
    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=destination,
        stderr=destination
    )
    io_tasks = []
    if destination_stream is not None:
        await asyncio.gather(
            copy_output(process, process.stdout, destination_stream),
            copy_output(process, process.stderr, destination_stream)
        )
    else:
        await process.wait()
    destination_stream.write(f'q {process.returncode}'.encode('ascii'))
    logger.info(f'[{program}] <exited with code {process.returncode}>')

async def command_loop(reader, writer):
    try:
        data = await reader.readline()
        if not data or data[:2] != b'e ':
            return
        program, *args = shlex.split(data[2:].decode('ascii').rstrip())
        await run(program, *args, destination_stream=writer)
    finally:
        writer.close()

async def serve(host, port):
    server = await asyncio.start_server(command_loop, host=host, port=port)
    async with server:
        await server.serve_forever()
