import asyncio
import logging
import shlex
import sys

logger = logging.getLogger('run_remote.client')

async def read_commands(source_stream):
    while True:
        data = await source_stream.readline()
        if not data:
            if source_stream.at_eof():
                break
            else:
                continue
        if data[:2] == b't ':
            print(data[2:].decode('ascii').rstrip())
        elif data[:2] == b'q ':
            return int(data[2:].decode('ascii'))

async def run(host, port, program, *args):
    command = shlex.join([program] + list(args))
    logger.info(f'[{program}] <starting>')
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(f'x {command}\n'.encode('ascii'))
    await writer.drain()
    exit_code = await read_commands(reader)
    writer.close()
    if exit_code is not None:
        logger.info(f'[{program}] <exited with code {exit_code}>')
    else:
        logger.error(f'[{program}] <exited with unknown code>')
    return exit_code
