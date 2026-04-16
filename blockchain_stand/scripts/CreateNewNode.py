#!/usr/bin/env python3

"""
    Данный скрипт предназначен для создания новых узлов в сети.

        Перед использованием данного скрипта нужно запустить InitializeNetwork.py.
    Это обязательное условие для использования следующих скриптов, которые
    написаны для стенда.

    Что делает скрипт:
        1. Проверяет была ли создана Docker-сеть с название blockchain_stand.
           Если сеть не была создана, то скрипт выводит предупреждение и прекращает
           свою работу.
        2. Проверяет создан ли файл genesis.json, а также проверяет его на корректность.
        3. Проверяет был ли создан валидатор, если был выбран алгоритм Clique.
           Это можно проверить, так как в файле genesis.json содержится эта информация.
        4. Создает аккаунт для узла.
        5. Создает сам узел и запускает его.


    Пример того как пользоваться данным скриптом:
        CreateNewNode.py <node_name> <http-порт> <p2p-порт> <пароль>
    
        Перед созданием обязательно проверять передаваемые порты, чтобы они не были заняты.
    Иначе Docker выкинет ошибку, что порт уже занят

        Также важно знать, что данный скрипт не связывает узел с другими.
    Чтобы связать ноды нужно воспользоваться скриптом ConnectNodes.py

"""


import json
import sys
import subprocess
import re
import ipaddress
from pathlib import Path

BASE_DIR = Path.home() / "blockchain_stand"
CONFIG_DIR = BASE_DIR / "config"
DOCKER_IMAGE = "ethereum/client-go:v1.13.15"
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
    commandForCheck = ["docker", "info"]

    output = subprocess.run(commandForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False


def CheckDockerNetwork():
    """

    """
    
    commandsForCheck = [
        "docker", "network", "ls", 
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if not output.stdout.strip():
        print("Err!: Docker-сеть не была создана!")
        print("Запустите скрипт InitializeNetwork.py, чтобы пользоваться данным скриптом")
        sys.exit(1)
    else:
        print(f"Docker-сеть {DOCKER_NETWORK} существует!")


def CheckGenesisFile(genesisPath):
    """
    """
    if not genesisPath.exists():
        print("Err!: genesis.json не найден!")
        print("Попробуйте запустить DeleteAll.py и после InitializeNetwork.py")
        sys.exit(1)
    
    with open(genesisPath, "r") as jsonFile:
        genesisFile = json.load(jsonFile)

    genesisConfig = genesisFile.get("config")
    
    if not genesisConfig:
        print("Err!: genesis.json был создан не правильно!")
        sys.exit(1)
    
    chainId = genesisConfig.get("chainId")

    if chainId is None:
        print("Err!: genesis.json был создан не правильно!")
        print("Отсутсвует chainId!")
        sys.exit(1)
    
    print(f"Chain ID: {chainId}")

    if "clique" in genesisConfig:
        extradata = genesisFile.get("extradata")

        if (len(extradata) < 2 + 64 + 40 + 130):
            print("Err!: genesis.json был создан не правильно!")
            print("Отсутствует или неправильно был назначен валидатор")
            sys.exit(1)
        
        print("Найдена сеть с алгоритмом Clique")
        return "clique"
    
    elif "ethash" in genesisConfig:
        print("Найдена сеть Ethash")
        return "ethash"
    
    else:
        print("Err!: genesis.json был создан не правильно!")
        print("Неизвестный алгоритм консенсуса или отсутсвует его поддержка")
        sys.exit(1)


def GetNextFreeIp():
    """
        Определяет следующий свободный IP в Docker сети до запуска контейнера. 
        
        Это позволяет передать точный IP для запуска клиента Geth.
            
            Это особенность самого клиента. Если запущенные контейнеры будут 
        не в одной сети, то они не смогут общаться с друг другом
    """

    # Команда позволяет извлечь детальную информацию о сети.
    # Из нее мы извлекаем json
    output = subprocess.run(
        ["docker", "network", "inspect", DOCKER_NETWORK,
         "--format", "{{json .}}"],
        capture_output=True, text=True
    )

    if output.returncode != 0:
        print("Err!: Не удалось получить информацию о Docker сети!")
        sys.exit(1)

    networkInfo = json.loads(output.stdout)

    # Получаем подсеть
    subNetwork = networkInfo["IPAM"]["Config"][0]["Subnet"]
    network = ipaddress.IPv4Network(subNetwork)
    gateway = networkInfo["IPAM"]["Config"][0].get("Gateway")

    # Собираем уже занятые IP
    usedIpAdrrs = set()

    # Сразу добавим шлюз, чтобы случайно его не занять
    if gateway:
        usedIpAdrrs.add(gateway)

    for container in networkInfo.get("Containers", {}).values():
        ip = container.get("IPv4Address", "").split("/")[0]
        if ip: usedIpAdrrs.add(ip)

    hosts = list(network.hosts())
    for host in hosts:
        if str(host) not in usedIpAdrrs:
            return str(host)

    print("Err!: Нет свободных IP в Docker сети!")
    sys.exit(1)


def getNetworkId():
    """
        Данная функция ищет ID сети через genesis.json
    """
    genesisPath = CONFIG_DIR / "genesis.json"

    if not genesisPath.exists():
        print("Err!: genesis.json не найден!")
        sys.exit(1)

    with open(genesisPath, "r") as jsonFile:
        genesisFile = json.load(jsonFile)

    chainId = genesisFile["config"]["chainId"]

    print(f"NetworkID: {chainId}")

    return chainId


def CreateAccount(dataDirectory, password):
    """
        Данная функция создает аккаунт для ноды.
    """
    dataDirectory.mkdir(parents=True, exist_ok=True)

    passwordFile = dataDirectory / "password.txt"
    passwordFile.write_text(password)

    commandsForCreate = [
        "docker", "run", "--rm",
        "-v", f"{dataDirectory}:/data",
        DOCKER_IMAGE, "account", "new",
        "--datadir", "/data", "--password",
        "/data/password.txt"
    ]

    result = RunCommands(commandsForCreate)

    publicKey = re.search(r'0x[0-9a-fA-F]{40}', result.stdout)

    if publicKey:
        addr = publicKey.group(0)
        print(f"Создан аккаунт: {addr}")
        return addr
    else:
        print("Err!: Не удалось создать аккаунт!")
        sys.exit(1)


def InitializeNode(dataDirectory):
    """
        Данная функция инициализирует ноду (создает БД с genesis.json)
    """
    genesisPath = CONFIG_DIR / "genesis.json"

    if not genesisPath.exists():
        print("Err!: genesis.json не найден!")
        print("     Нужно сначала запустить InitNetwork.py")
        sys.exit(1)

    commands = [
        "docker", "run", "--rm",
        "-v", f"{CONFIG_DIR}:/config",
        "-v", f"{dataDirectory}:/data",
        DOCKER_IMAGE,
        "init", "--datadir", "/data",
        f"/config/{genesisPath.name}"
    ]

    RunCommands(commands)
    print("База данных инициализирована")


def StartNode(nodeName, httpPort, p2pPort, dataDirectory):
    """
        Данная функция запускает ноду с выделенным свободным IP
        в Docker сети.
    """

    genesisPath = CONFIG_DIR / "genesis.json"
    chainId = getNetworkId()
    containerName = f"geth-{nodeName}"

    # Определяем свободный IP
    dockerIp = GetNextFreeIp()
    print(f"IP: {dockerIp}")

    RunCommands([
        "docker", "run", "-d",
        "--name", containerName,
        "--network", DOCKER_NETWORK,
        f"--ip={dockerIp}",
        "-p", f"{httpPort}:8545",
        "-p", f"{p2pPort}:30303",
        "-v", f"{genesisPath}:/config/genesis.json:ro",
        "-v", f"{dataDirectory}:/data",
        DOCKER_IMAGE,
        "--datadir=/data",
        "--ipcpath", "/data/geth.ipc",
        f"--networkid={chainId}",
        "--http",
        "--http.addr=0.0.0.0",
        "--http.port=8545",
        "--http.api=eth,net,web3,admin",
        "--http.corsdomain=*",
        "--allow-insecure-unlock",
        "--nodiscover",
        f"--nat=extip:{dockerIp}",
    ])

    print(f"Нода {nodeName} запущена на порту {httpPort} (не связанная)")


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)

    if len(sys.argv) < 5:
        print("Err!: Недостаточно аргументов")
        print("Пример: AddNode.py <node_name> <http-порт> <p2p-порт> <пароль>")
        sys.exit(1)

    nodeName = sys.argv[1]
    httpPort = sys.argv[2]
    p2pPort = sys.argv[3]
    password = sys.argv[4]

    genesisPath = CONFIG_DIR / "genesis.json"

    dataDir = BASE_DIR / "nodes" / nodeName / "data"

    CheckDockerNetwork()
    print()

    CheckGenesisFile(genesisPath)
    print()


    print("Создание изолированной ноды:")
    print(f"    HTTP: {httpPort}")
    print(f"    P2P: {p2pPort}\n\n")

    print("Создание аккаунта:")
    address = CreateAccount(dataDir, password)

    print("\nИнициализация ноды:")
    InitializeNode(dataDir)

    print("\nЗапуск ноды:")
    StartNode(nodeName, httpPort, p2pPort, dataDir)

    print("\n\nНода запущена:")
    print(f"Данные: {dataDir}")
    print(f"Адрес: {address}")
    print(f"Пароль: {password}")
    print(f"HTTP: http://localhost:{httpPort}")


if __name__ == "__main__":
    main()