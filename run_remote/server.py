import asyncio
import shlex
import sys

async def copy_output(process, source_stream, destination_stream):
    while process.returncode is None:
        data = await source_stream.readline()
        if not data:
            if source_stream.at_eof():
                break
            else:
                continue
        destination_stream.write(data)
        await destination_stream.drain()

async def run(program, *args, output_stream=None, errput_stream=None):
    if output_stream is None:
        stdout_destination = asyncio.subprocess.DEVNULL
    else:
        stdout_destination = asyncio.subprocess.PIPE
    if errput_stream is None:
        stderr_destination = asyncio.subprocess.DEVNULL
    else:
        stderr_destination = asyncio.subprocess.PIPE
    print(f'[{program}] <starting>')
    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=stdout_destination,
        stderr=stderr_destination
    )
    io_tasks = []
    if output_stream is not None:
        io_tasks.append(asyncio.create_task(copy_output(process, process.stdout, output_stream)))
    if errput_stream is not None:
        io_tasks.append(asyncio.create_task(copy_output(process, process.stderr, errput_stream)))
    if io_tasks:
        await asyncio.gather(*io_tasks)
    else:
        await process.wait()
    print(f'[{program}] <exited with code {process.returncode}>')

async def command_loop(reader, writer):
    data = await reader.readline()
    if not data:
        return
    program, *args = shlex.split(data.decode('ascii').rstrip())
    await run(program, *args, output_stream=writer, errput_stream=writer)
    writer.close()

async def serve(host, port):
    server = await asyncio.start_server(command_loop, host=host, port=port)
    async with server:
        await server.serve_forever()
