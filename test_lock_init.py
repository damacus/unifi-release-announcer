import asyncio
import sys
print(sys.version)

class Foo:
    def __init__(self):
        self.lock = asyncio.Lock()

f = Foo()
print("Success without running loop")

async def main():
    f2 = Foo()
    async with f2.lock:
        print("Success inside running loop")

asyncio.run(main())
