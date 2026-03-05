import re

with open('state_manager.py', 'r') as f:
    content = f.read()

# Add a lock in __init__
if 'self._lock = asyncio.Lock()' not in content:
    init_match = re.search(r'self\._state: dict\[str, str\] = \{\}\n\s+self\._load_state\(\)', content)
    if init_match:
        old_init = init_match.group(0)
        new_init = old_init + '\n        self._lock = asyncio.Lock()'
        content = content.replace(old_init, new_init)

# Use the lock in _save_state
if 'async with self._lock:' not in content:
    save_match = re.search(r'async def _save_state\(self\) -> None:\n\s+"""Save state to JSON file asynchronously\."""\n\s+await asyncio\.to_thread\(self\._sync_save\)', content)
    if save_match:
        old_save = save_match.group(0)
        new_save = '    async def _save_state(self) -> None:\n        """Save state to JSON file asynchronously."""\n        async with self._lock:\n            await asyncio.to_thread(self._sync_save)'
        content = content.replace(old_save, new_save)

with open('state_manager.py', 'w') as f:
    f.write(content)
