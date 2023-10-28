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

*Version: 0.6.0*

Manager your Dell PowerEdge Fan Speed with this handy tool!

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

Dockerfile
```dockerfile
FROM ubuntu:latest AS ubuntu
RUN apt update && apt upgrade -y && apt install -y dos2unix lm-sensors ipmitool wget curl git python3 python-is-python3 python3-pip gcc
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade fan-manager
CMD ["fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24"]
```

Docker Compose
```docker-compose
---
version: '3.9'

services:
  server_fan_speed:
    build: .
    container_name: server_fan_speed
    privileged: true
    volumes:
      - /dev/ipmi0:/dev/ipmi0
    restart: unless-stopped
```

Docker Run
```bash
docker run -it -d server_fan_speed fan-manager
```

Docker Compose
```bash
docker-compose up --build -d
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
