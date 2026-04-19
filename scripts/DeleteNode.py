import subprocess
import shutil
import sys
from pathlib import Path

BASE_DIR = Path.home() / "blockchain_stand"
DOCKER_NETWORK = "blockchain_stand"


def CheckDockerRun():
    commandsForCheck = ["docker", "info"]

    output = subprocess.run(commandsForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False


def DeleteContainer(node):
    containerName = f"geth-{node}"

    commandForCheck = [
        "docker", "ps", "-a", "-q", "-f",
        f"name={containerName}"
    ]

    commandForStop = ["docker", "stop", containerName]

    commandForDelete = ["docker", "rm", containerName]

    output = subprocess.run(commandForCheck, capture_output=True, text=True)

    if not output.stdout.strip():
        print(f"Контейнер {containerName} не существует!")
        return False
    
    output = subprocess.run(commandForStop, capture_output=True, text=True)

    output = subprocess.run(commandForDelete, capture_output=True, text=True)

    if output.returncode == 0:
        print(f"Узел {containerName} удален!")
        return True
    
    print("Ошибка при удалении!")
    return False


def DeleteNodeData(node):
    dataDir = BASE_DIR / "nodes"

    nodeDir = dataDir / "data"

    commandsForDelete = [
        "sudo", "rm", "-rf", str(nodeDir)
    ]

    if not dataDir.exists():
        print(f"Каталог {dataDir} не найден!")
        return False
    
    print("Удаление данных:")
    output = subprocess.run(commandsForDelete, capture_output=True)

    if output.returncode == 0:
        print(f"Узел {node} удален!")
        return True
    else:
        print("Err!")
        return False


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)
    
    DeleteContainer(sys.argv[1])

    DeleteNodeData(sys.argv[1])


if __name__ == "__main__":
    main()
