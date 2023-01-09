# Fan-Manager
*Version: 0.0.1*

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
```bash
fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24
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
