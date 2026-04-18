#!/usr/bin/env python3

"""
    Данный скрипт полностью очищает лабораторный стенд.

    Его обязательно нужно использовать перед созданием нового стенда.


    Что делает скрипт:
        1. Он останавливает и удаляет все контейнеры в сети.
        2. Удаляет Docker сети
        3. Удаляет конфиги и данные об узлах

    Все созданные контейнеры имеют префикс 'geth-'

    Для удаления данных спрашивается пароль администратора!
"""

import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path.home() / "blockchain_stand"
DOCKER_NETWORK = "blockchain_stand"


def CheckDockerRun():
    commandForCheck = ["docker", "info"]

    output = subprocess.run(commandForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False


def DeleteContainers():
    """ Функция удаляет и останавливает контейнеры """
    
    commandsForFindContainers = [
        "docker", "ps", "-a", "--format", "{{.Names}}"
    ]
 
    output = subprocess.run(
        commandsForFindContainers,
        capture_output=True, text=True
    )
 
    containers = [
        name for name in output.stdout.split()
        if name.startswith("geth-")
    ]
 
    if not containers:
        print("Нету узлов для удаления")
        return
 
    for container in containers:
        print(f"Удаление узла: {container}")
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    
    print(f"\nКоличество удаленных контейнеров: {len(containers)}")


def DeleteDockerNet():
    """
        Функция удаляет Docker сеть, в которой запущены узлы
    """

    commandsForCheck = [
        "docker", "network", "ls",
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    commandsForDelete = [
        "docker", "network", "rm",
        DOCKER_NETWORK
    ]

    output = subprocess.run(
        commandsForCheck, capture_output=True,
        text=True
    )

    if output.stdout.strip():
        print(f"Удаление Docker-сети: {DOCKER_NETWORK}")
        
        subprocess.run(
            commandsForDelete, capture_output=True
        )
    else:
        print(f"Docker-сеть {DOCKER_NETWORK} не найдена!")
    

def DeleteAllData():
    """
        Удаляет папки config и nodes из стенда.
 
        В папке config содержится genesis.json.
 
        В папке nodes данные об узлах.
    """
 
    pathForDelete_1 = BASE_DIR / "config"
    pathForDelete_2 = BASE_DIR / "nodes"
 
    if pathForDelete_1.exists():
        print(f"Удаление каталога: {pathForDelete_1}")
        subprocess.run(["sudo", "rm", "-rf", pathForDelete_1])
    else:
        print(f"Путь {pathForDelete_1} не найден!")
 
 
    if pathForDelete_2.exists():
        print(f"Удаление каталога: {pathForDelete_2}")
        subprocess.run(["sudo", "rm", "-rf", pathForDelete_2])
    else:
        print(f"Путь {pathForDelete_2} не найден!")


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        print("\nЗапускается простое удаление данных!")
        DeleteAllData()
        print("\nОбязательно после запуска докера проверьте запущенные контейнеры и сеть")
        print("Если что-то есть, то скрипт нужно запустить ещё раз")
        return

    
    print("Очистка стенда!")

    print("\nУдаление узлов:")
    DeleteContainers()

    print(f"\nУдаление Docker-сети {DOCKER_NETWORK}:")
    DeleteDockerNet()

    print("\nУдаление данных:")
    DeleteAllData()


    print("\n\nСтенд очищен!")


if __name__ == "__main__":
    main()
    