#!/usr/bin/env python

import asyncio
import shlex
import sys

async def copy_output(process, stream, prefix):
    while process.returncode is None:
        data = await stream.readline()
        if not data:
            if stream.at_eof():
                break
            else:
                continue
        print('{}: {}'.format(prefix, data.decode('ascii').rstrip()))

async def run(program, *args):
    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE # TODO maybe change this
    )
    await asyncio.gather(
        copy_output(process, process.stdout, f'[{program}:1]'),
        copy_output(process, process.stderr, f'[{program}:2]')
    )
    print(f'[{program}] <exited with code {process.returncode}>')

async def command_loop(reader, writer):
    data = await reader.readline()
    program, *args = shlex.split(data.decode('ascii').rstrip())
    await run(program, *args)

async def main():
    server = await asyncio.start_server(command_loop, host='localhost', port=13180) # same port from RemoteForward SSH directive (see ~/.ssh/config)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass # TODO wait for processes
