import asyncio

class TestClass:
    def __init__(self):
        self.lock = asyncio.Lock()

def sync_init():
    t = TestClass()
    print("Init sync successful")
    return t

async def run():
    t = sync_init()
    async with t.lock:
        print("Lock acquired")

asyncio.run(run())
