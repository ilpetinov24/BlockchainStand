import json
import sys
import subprocess
import re
import ipaddress
from pathlib import Path


BASE_DIR = Path.home() / "blockchain_stand"
CONFIG_DIR = BASE_DIR / "config"
DOCKER_NETWORK = "blockchain_stand"
DOCKER_IMAGE = "ethereum/client-go:v1.13.15"

from Functions import *

def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)
    
    DeleteContainer(sys.argv[1])

    DeleteNodeData(sys.argv[1])


if __name__ == "__main__":
    main()
