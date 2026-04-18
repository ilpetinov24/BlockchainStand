#!/usr/bin/env python3

"""
    Данный скрипт выводит информацию о всей Docker-сети blockchain_stand

    Что именно выводится:
        1. 

"""

import json
import sys
import subprocess
import re
import ipaddress
from pathlib import Path


BASE_DIR = Path.home() / "blockchain_stand"
DOCKER_NETWORK = "blockchain_stand"


def RunCommands(commands):
    """
        Функция для запуска комманд в консоле без вывода результата.
    """

    output = subprocess.run(commands, capture_output=True, text=True)

    if output.returncode != 0:
        print(f"Err!: {output.stderr}")
        sys.exit(1)

    return output


def CheckDockerRun():
    """
        Функция для проверки Docker. Проверяет запущен ли он или нет.
    """
    commandForCheck = ["docker", "info"]

    output = subprocess.run(commandForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False


def ShowNetworkInfo():
    """
        Данная функция выводит информацию о Docker-сети blockchain_stand
    """

    commandsForCheck = [
        "docker", "network", "ls", 
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if not output.stdout.strip():
        print("Docker-сеть blockchain_stand не существует!")
        sys.exit(1)
    
    print("Информация о Docker-сети: ")

    commandsForCheck = [
        "docker", "network", "inspect", DOCKER_NETWORK
    ]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if output.returncode != 0:
        print("Err!: Не удалось получить информацию о Docker-сети!")
        sys.exit(1)
    

    netInfo = json.loads(output.stdout)[0]

    print(f"Имя сети: {netInfo.get("Name")}")
    ipam = netInfo.get("IPAM", {})
    config = ipam.get("Config", [{}])[0]
    print(f"Subnet: {config.get("Subnet")}")
    print(f"Gateway: {config.get("Gateway")}")

    print(f"Узлов в сети: {len(netInfo.get("Containers"))}")


def main():
    ShowNetworkInfo()


if __name__ == "__main__":
    main()


