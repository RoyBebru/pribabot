#!/usr/bin/env python3

from aiofile import async_open
import asyncio
import os
import sys
import websockets

async def hello():
    uri = "ws://localhost:8765"
    try:
        async with async_open("main_client.log", 'w+') as afp:
            try:
                async with websockets.connect(uri) as websocket:
                    while True:
                        try:
                            command = input(">>> ").strip()
                        except (KeyboardInterrupt, EOFError): # Ctrl+C/D
                            print()
                            break

                        if command == '.' \
                                or command.lower() == 'exit' \
                                or command.lower() == 'quit':
                            break

                        try:
                            await websocket.send(command)
                            # print(f">>> {command}")
                            echo = await websocket.recv()
                            print(echo)
                            await afp.write(f">>> {command}"
                                            + os.linesep 
                                            + echo + os.linesep)
                        except Exception as e:
                            print(f"Cought error: {str(e)}", file=sys.stderr)
            except ConnectionRefusedError as e:
                print(f"Access to '{uri}' problem: {str(e)}", file=sys.stderr)
    except (PermissionError, FileNotFoundError) as e:
        print(f"Cannot open file: {str(e)}")

if __name__ == "__main__":
    asyncio.run(hello())
