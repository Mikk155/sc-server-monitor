# Sven Co-op Dedicated Server Monitor

A robust, lightweight Python-based automated monitoring system designed specifically for **Sven Co-op Dedicated Servers (`svends.exe`)**. 

Unlike simple process-checkers, this monitor uses real-time **A2S_INFO UDP network queries (HLQuery protocol)** to detect not only complete crashes but also **silent server freezes** (such as infinite code loops caused by unstable AMX Mod X plugins). If a server stops responding to network queries, the script forcefully kills its entire process tree and cleanly restarts it.

## Features

- **Anti-Freeze Detection:** Sends UDP network queries directly to the GoldSrc engine to guarantee the server is actually processing frames.
- **Port-Based Window Titles:** Automatically sets the native Windows command console title to `Port XXXX` for straightforward identification.
- **Correct Working Directory Binding:** Launches servers natively inside the root directory to guarantee configuration files and maps (like `hl_c04`) initialize seamlessly.
- **JSON Schema Validation:** Includes full JSON Schema support for auto-completion and syntax checks within modern IDEs.

## Installation

To ensure proper relative path mapping, you must install this utility directly within your game structure.

1. Drop the monitor folder into your main game directory, naming it exactly **`sc-server-monitor`**:
   ```text
   Sven Co-op/
   ├── svends.exe
   ├── svencoop/
   └── sc-server-monitor/
       └── src/
           ├── config.json
           ├── main.py
           ├── requirements.txt
           └── schema.json
   ```

2. Open your terminal or command prompt, navigate to the folder, install dependencies, and run the controller:
   ```bash
   cd src
   pip install -r requirements.txt
   python main.py
   ```

## Configuration Example (`config.json`)

Configure your dedicated instances using clear objects. The script manages formatting constraints behind the scenes:

```json
{
    "$schema": "schema.json",
    "servers":
    [
        {
            "app": "svends.exe",
            "port": 27018,
            "map": "hl_c04",
            "args": [
                "-netthread",
                "-console",
                "+maxplayers", "32"
            ]
        }
    ]
}
```
