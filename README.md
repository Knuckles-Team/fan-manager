# Fan-Manager
*Version: 0.1.0*

Manager your Dell PowerEdge Fan Speed with this handy tool!

### Usage:
| Short Flag | Long Flag   | Description                                            |
|------------|-------------|--------------------------------------------------------|
| -h         | --help      | See usage for fan-manager                              | 
| -i         | --intensity | Intensity of Fan Speed - Scales Logarithmically (0-10) | 
| -c         | --cold      | Minimum Temperature for Fan Speed                      | 
| -w         | --warm      | Maximum Temperature for Fan Speed                      | 
| -s         | --slow      | Minimum Fan Speed                                      | 
| -f         | --fast      | Maximum Fan Speed                                      | 
| -p         | --poll-rate | Poll Rate for CPU Temperature in Seconds               | 

### Example:

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

#### Install Instructions
Install Python Package

```bash
python -m pip install fan-manager
```

#### Build Instructions
Build Python Package

```bash
sudo chmod +x ./*.py
sudo pip install .
python3 setup.py bdist_wheel --universal
# Test Pypi
twine upload --repository-url https://test.pypi.org/legacy/ dist/* --verbose -u "Username" -p "Password"
# Prod Pypi
twine upload dist/* --verbose -u "Username" -p "Password"
```
