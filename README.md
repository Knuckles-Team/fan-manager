# Fan-Manager

![PyPI - Version](https://img.shields.io/pypi/v/fan-manager)
![PyPI - Downloads](https://img.shields.io/pypi/dd/fan-manager)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/fan-manager)
![GitHub forks](https://img.shields.io/github/forks/Knuckles-Team/fan-manager)
![GitHub contributors](https://img.shields.io/github/contributors/Knuckles-Team/fan-manager)
![PyPI - License](https://img.shields.io/pypi/l/fan-manager)
![GitHub](https://img.shields.io/github/license/Knuckles-Team/fan-manager)

![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/fan-manager)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Knuckles-Team/fan-manager)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/Knuckles-Team/fan-manager)
![GitHub issues](https://img.shields.io/github/issues/Knuckles-Team/fan-manager)

![GitHub top language](https://img.shields.io/github/languages/top/Knuckles-Team/fan-manager)
![GitHub language count](https://img.shields.io/github/languages/count/Knuckles-Team/fan-manager)
![GitHub repo size](https://img.shields.io/github/repo-size/Knuckles-Team/fan-manager)
![GitHub repo file count (file type)](https://img.shields.io/github/directory-file-count/Knuckles-Team/fan-manager)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/fan-manager)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/fan-manager)

*Version: 0.6.3*

Manager your Dell PowerEdge Fan Speed with this handy tool!

MCP Server for Agentic AI! Get started with Pip or Docker as well

This repository is actively maintained - Contributions are welcome!

Contribution Opportunities:
- Increase support of Dell PowerEdge Devices
- Support Non-PowerEdge Devices
- Support Non-Dell Devices

<details>
  <summary><b>Usage:</b></summary>

| Short Flag | Long Flag   | Description                                            |
|------------|-------------|--------------------------------------------------------|
| -h         | --help      | See usage for fan-manager                              |
| -i         | --intensity | Intensity of Fan Speed - Scales Logarithmically (0-10) |
| -c         | --cold      | Minimum Temperature for Fan Speed                      |
| -w         | --warm      | Maximum Temperature for Fan Speed                      |
| -s         | --slow      | Minimum Fan Speed                                      |
| -f         | --fast      | Maximum Fan Speed                                      |
| -p         | --poll-rate | Poll Rate for CPU Temperature in Seconds               |

</details>

<details>
  <summary><b>Example:</b></summary>

Python
```bash
fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24
```

Docker Compose

Fan Manager
```docker-compose
---
services:
  fan-manager:
    image: knucklessg1/fan-manager:latest
    container_name: server_fan_speed
    privileged: true
    environment:
      MODE: "fan-manager"
      INTENSITY: ${INTENSITY}
      COLD: ${COLD}
      WARM: ${WARM}
      SLOW: ${SLOW}
      FAST: ${FAST}
      POLL_RATE: ${POLL_RATE}
    volumes:
      - /dev/ipmi0:/dev/ipmi0
    restart: unless-stopped
```

Fan Manager MCP Server
```docker-compose
---
services:
  fan-manager-mcp:
    image: knucklessg1/fan-manager:latest
    container_name: server_fan_speed
    privileged: true
    environment:
      MODE: "fan-manager-mcp"
      HOST: 0.0.0.0
      PORT: 8030
      TRANSPORT: "http"
    volumes:
      - /dev/ipmi0:/dev/ipmi0
    restart: unless-stopped
```

Docker Run
```bash
docker run -it -d knucklessg1/fan-manager:latest fan-manager
```

Docker Compose
```bash
docker-compose up --build -d
```

## Use with AI

Configure `mcp.json`

Recommended: Store secrets in environment variables with lookup in JSON file.

For Testing Only: Plain text storage will also work, although **not** recommended.

```json
{
  "mcpServers": {
    "fan-manager": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fan-manager",
        "fan-manager-mcp"
      ],
      "timeout": 200000
    }
  }
}
```

</details>

<details>
  <summary><b>Installation Instructions:</b></summary>

Install Python Package

```bash
python -m pip install fan-manager
```

</details>

<details>
  <summary><b>Repository Owners:</b></summary>


<img width="100%" height="180em" src="https://github-readme-stats.vercel.app/api?username=Knucklessg1&show_icons=true&hide_border=true&&count_private=true&include_all_commits=true" />

![GitHub followers](https://img.shields.io/github/followers/Knucklessg1)
![GitHub User's stars](https://img.shields.io/github/stars/Knucklessg1)
</details>
