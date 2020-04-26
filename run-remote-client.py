#!/usr/bin/env python3.8

import argparse
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

def parse_arguments():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True, dest='subcommand', title='subcommands')
    run_parser = subparsers.add_parser('run', help='Run a command on the remote host')
    run_parser.add_argument('--host', action='store', default='localhost', help='Hostname or IP address to connect to')
    run_parser.add_argument('-p', '--port', action='store', type=int, default=13180, help='Port to connect to')
    run_parser.add_argument('command', help='Command to run')
    run_parser.add_argument('arguments', nargs=argparse.REMAINDER, help='Arguments for the command')

    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.subcommand == 'run':
        try:
            asyncio.run(run(args.host, args.port, args.command, *args.arguments))
        except KeyboardInterrupt:
            pass # TODO wait for process

if __name__ == '__main__':
    main()
