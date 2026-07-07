# Palworld Server Discord Bot

A production-quality Discord bot written in Python 3.13+ using `discord.py` that manages a Google Compute Engine (GCE) VM hosting a Palworld dedicated server. It offers automatic startup sequence verification, status monitoring, active player counts/latency querying, and admin-only graceful shutdown capabilities.

## Architecture & Features

- **Asynchronous Design**: The entire bot uses `async/await` patterns. Heavy I/O bound libraries like Google Compute client are executed inside a separate thread pool (`asyncio.to_thread`) to ensure the Discord event loop remains responsive.
- **REST API Integration**: Communicates directly with the Palworld Dedicated Server's REST API using `aiohttp` to check metrics, list active players, and trigger graceful, save-safe shutdown commands.
- **Security & Channel Lock**: Restricted to a configurable command channel and a target role. Admins alone have privilege to shut down the server.
- **Abuse Protection**: Configurable command cooldowns prevent bot spamming.

---

## Folder Structure

```
palworld-server-discord-bot/
├── bot.py                  # Main entrypoint and extension loader
├── config.py               # Config parsing and env validation
├── requirements.txt        # Third-party dependency definitions
├── .env.example            # Template configurations
├── README.md               # User guide
│
├── commands/               # Modular Command extensions (Cogs)
│   ├── start.py
│   ├── status.py
│   ├── players.py
│   ├── stop.py
│   └── help.py
│
├── services/               # Modular integration layers
│   ├── gcp.py              # Google Cloud GCE controls
│   ├── palworld.py         # Palworld Dedicated Server REST client
│   └── permissions.py      # Channel and role enforcement check decorators
│
├── utils/                  # Core helpers
│   ├── embeds.py           # Standardized embed message formats
│   ├── logger.py           # Structured logger setup
│   └── cooldown.py         # Custom dynamic cooldown manager
│
└── tests/                  # Unit and integration test suites
```

---

## Prerequisites & Installation

### 1. Requirements

- Python 3.13+ installed.
- **GCP credentials**: The environment running the bot must have access to manage Compute Engine. Typically, this is achieved by installing the Google Cloud CLI and authenticating via Application Default Credentials (ADC):
  ```bash
  gcloud auth application-default login
  ```
  Or by exporting the path to a service account json credential file:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
  ```

### 2. Palworld Server Setup

Enable the REST API inside your Palworld server configuration file (e.g. `PalWorldSettings.ini` under `Pal/Saved/Config/LinuxServer/` or `WindowsServer/`):

```ini
RESTAPIEnabled=True
RESTAPIPort=8212
AdminPassword="YourStrongPassword"
```
*Note: Basic Auth username defaults to `admin`.*

### 3. Installation Steps

1. Clone the repository and navigate to the folder.
2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Fill out the required configuration options in `.env`:
   - `DISCORD_TOKEN`: Discord Developer Portal Bot token.
   - `GCP_PROJECT_ID`: Google Cloud Project ID hosting the VM.
   - `GCP_ZONE`: Zone of the target VM (e.g. `us-central1-a`).
   - `INSTANCE_NAME`: GCE instance name.
   - `ALLOWED_ROLE`: The Discord role name or ID permitted to run start/status/players commands.
   - `ALLOWED_CHANNEL_ID`: Channel ID restricted for command execution.
   - `PALWORLD_REST_URL`: The URL to access the REST API (e.g. `http://<VM-External-IP>:8212` or localhost).
   - `PALWORLD_REST_USERNAME`: Defaults to `admin`.
   - `PALWORLD_REST_PASSWORD`: Matches `AdminPassword` in `PalWorldSettings.ini`.

---

## Running the Bot

To start the bot, run the main script:

```bash
python bot.py
```

Upon startup, the bot will validate the environment variables, load all extensions, sync slash commands globally with Discord, and login.

---

## Commands Reference

- **/start**: Starts the virtual machine if it's currently stopped. Once online, it waits for the Palworld REST API to become ready, reporting total startup time and connection details.
- **/status**: Displays the GCE VM state, Palworld API state, server FPS, server uptime, current players count, and external IP.
- **/players**: Returns details (Steam ID, level, latency) of all players currently connected.
- **/stop**: (Administrator only) Gracefully shuts down the Palworld server process (performing world-saves) and halts the GCE virtual machine. Refuses execution if players are currently logged in.
- **/help**: Displays bot information, channel lock information, and command guide.
