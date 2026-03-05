import re

with open('state_manager.py', 'r') as f:
    content = f.read()

# Make sure set_last_url is not using _save_state directly or we can just use the lock in set_last_url instead
# Actually, the user is right! If multiple events are processed concurrently, one coroutine could be writing while another updates `self._state`, leading to inconsistent JSON writes (e.g. dict mutated during iteration by json.dump!).

# Wait, `json.dump` iterates over `self._state`. If another task yields and updates `self._state` while `_sync_save` is running in another thread, it will raise `RuntimeError: dictionary changed size during iteration`.

# To prevent this, we should hold an `asyncio.Lock` when modifying the dict AND saving it.
# BUT we can't block the event loop. `asyncio.Lock` only guards async sections. The synchronous thread doesn't hold the `asyncio.Lock`, it runs in an executor!
# Wait, if we use `async with self._lock:` inside the async loop, no other async task can enter the critical section until the thread completes!
# So no other task can modify `self._state` while `_save_state` is running, provided they also need to acquire the lock to modify `self._state`!

# So we should acquire the lock inside `set_last_url`!

# Let's rewrite `set_last_url`:
new_set_last_url = """    async def set_last_url(self, tag: str, url: str) -> None:
        \"\"\"
        Set the last posted URL for a tag.

        Args:
            tag: The tag to set URL for
            url: The URL to store
        \"\"\"
        async with self._lock:
            self._state[tag] = url
            await asyncio.to_thread(self._sync_save)"""

content = re.sub(r'    async def set_last_url\(self, tag: str, url: str\) -> None:.*?await self\._save_state\(\)', new_set_last_url, content, flags=re.DOTALL)

# Delete async def _save_state as it is no longer needed
content = re.sub(r'    async def _save_state\(self\) -> None:\n.*?await asyncio\.to_thread\(self\._sync_save\)', '', content, flags=re.DOTALL)

with open('state_manager.py', 'w') as f:
    f.write(content)
