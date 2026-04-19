#!/usr/bin/env python3

"""
    Данный скрипт 
"""

import json
import sys
import subprocess
import re
from pathlib import Path

from ConnectNodes import *


def GetNodes():
    nodes = []

    commandsForGet = [
        "docker", "ps", "--filter", "name=geth-",
        "--format", "{{.Names}}"
    ]

    output = subprocess.run(commandsForGet, capture_output=True, text=True)

    if not output.stdout.strip():
        return nodes

    for container in output.stdout.strip().split("\n"):
        if container:
            nodes.append(container.replace("geth-", ""))
    
    return nodes


def ConnectAllNodes():
    nodes = GetNodes()

    if (len(nodes) < 2):
        print("Запущена всего одна нода!")
        sys.exit(1)
    
    print(f"Всего узлов: {len(nodes)}")

    enodes = {}

    for node in nodes:
        enode = GetEnode(node)

        if not enode:
            print(f"Err!: Не удалось получить enode для {node}")
            continue

        enodes[node] = enode
        print(f"{node}: {enode}")

    print("Подключаем ноды")

    totalConnected = 0

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            firstNode = nodes[i]
            secondNode = nodes[j]
    
            if AddPeer(firstNode, enodes[secondNode]):
                totalConnected += 1
                print(f"Подключено: {firstNode} <-> {secondNode}")
            else:
                print(f"Не удалось подключить {firstNode} к {secondNode}")
    
    print(f"Выполнено подключений {totalConnected}")


def main():
    if not CheckDockerRun():
        print("Err!: Docker не запущен")
        sys.exit(1)
    
    ConnectAllNodes()


if __name__ == "__main__":
    main()
        
