#!/usr/bin/env python3.8

import asyncio
import shlex
import sys

async def print_output(source_stream):
    while True:
        data = await source_stream.readline()
        if not data:
            if source_stream.at_eof():
                break
            else:
                continue
        print(data.decode('ascii').rstrip())

async def run(port, program, *args):
    command = shlex.join([program] + list(args))
    print(f'[{program}] <starting>')
    reader, writer = await asyncio.open_connection('localhost', port)
    writer.write((command + '\n').encode('ascii'))
    await writer.drain()
    await print_output(reader)
    writer.close()
    print(f'[{program}] <exited>')

async def main():
    port = int(sys.argv[1])
    await run(port, *sys.argv[2:])

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass # TODO wait for process
