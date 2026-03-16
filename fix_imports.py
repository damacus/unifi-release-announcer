with open("release_parser.py") as f:
    content = f.read()

# Clean up floating import
content = content.replace("from typing import Any\n\n\ndef load_releases", "def load_releases")

# Add to top
if "from typing import Any" not in content[:200]:
    content = content.replace(
        "from datetime import datetime\n", "from datetime import datetime\nfrom typing import Any\n"
    )

with open("release_parser.py", "w") as f:
    f.write(content)
