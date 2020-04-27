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

async def run(host, port, program, *args):
    command = shlex.join([program] + list(args))
    print(f'[{program}] <starting>')
    reader, writer = await asyncio.open_connection(host, port)
    writer.write((command + '\n').encode('ascii'))
    await writer.drain()
    await print_output(reader)
    writer.close()
    print(f'[{program}] <exited>')
