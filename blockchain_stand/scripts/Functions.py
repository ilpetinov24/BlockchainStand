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

# Убрать функцию
def RunCommands(commands):
    """
        Функция для запуска комманд в консоле без вывода результата.
    """

    output = subprocess.run(commands, capture_output=True, text=True)

    if output.returncode != 0:
        print(f"Err!: {output.stderr}")
        sys.exit(1)

    return output


# Готово
def CheckNode(nodeName):
    """
        Данная функция проверяет, что нода существует и запущена.

        Возвращает true, если узел существует и запущен. В другом случае возращает false
    """

    commandsForCheck = ["docker", "ps", "-q", "-f", f"name=geth-{nodeName}"]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if output.stdout.strip():
        return True
    
    return False

# Готово
def CheckDockerRun():
    commandsForCheck = ["docker", "info"]

    output = subprocess.run(commandsForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False

def CheckDockerNetwork():
    """
        Функция для проверки Docker-сети.

        Проверяет запущена ли сеть с название blockchain-stand.
        Если сеть не запущена, то скрипт завершает работу.
    """
    
    commandsForCheck = [
        "docker", "network", "ls", 
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if not output.stdout.strip():
        return False
    
    return True

# Готов
def CreateDockerNetwork():
    """
        Создаёт Docker сеть для узлов, если она ещё не была создана.

        Возращает true, если сеть создана или уже была создана. В другом случае возвращает false
    """
    
    # Команда выводит только ID сети
    commandsForCheck = [
        "docker", "network", "ls", 
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    commandsForCreate = ["docker", "network", "create", DOCKER_NETWORK]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    # Проверяем есть ли ID
    if output.stdout.strip():
        print(f"Docker-сеть {DOCKER_NETWORK} уже существует!")
        return True
    
    output = subprocess.run(commandsForCreate, capture_output=True, text=True)
    
    if output.returncode == 0:
        return True # Сеть создана
    
    return False # Создать сеть не удалось по другим причинам


def GetNextFreeIp():
    """
        Определяет следующий свободный IP в Docker сети до запуска контейнера. 
        
        Это позволяет передать точный IP для запуска клиента Geth.
            
            Это особенность самого клиента. Если запущенные контейнеры будут 
        не в одной сети, то они не смогут общаться с друг другом.

            Функция возвращает свободный IP-адрес. В случае неудачи возвращает None.
        При этом функция выводит причину ошибки.
    """

    # Команда позволяет извлечь детальную информацию о сети.
    # Из нее мы извлекаем json
    output = subprocess.run(
        ["docker", "network", "inspect", DOCKER_NETWORK,
         "-f", "{{json .}}"],
        capture_output=True, text=True
    )

    if output.returncode != 0:
        print("Err!: Не удалось получить информацию о Docker сети!")
        return None

    networkInfo = json.loads(output.stdout)

    # Получаем подсеть (Обычно 172.18.0.0/16)
    subNetwork = networkInfo["IPAM"]["Config"][0]["Subnet"]
    network = ipaddress.IPv4Network(subNetwork)

    gateway = networkInfo["IPAM"]["Config"][0].get("Gateway")

    # Собираем уже занятые IP
    usedIp = set()

    # Сразу добавим шлюз, чтобы случайно его не занять
    if gateway:
        usedIp.add(gateway)
    else:
        print("Err!: Не удалось получить полную информацию о сети!")
        return None
    
    for container in networkInfo.get("Containers", {}).values():
        ip = container.get("IPv4Address", "").split("/")[0] # Маска нам не нужна
        if ip: usedIp.add(ip)

    # Возвращаем первый свободный IP.    
    for host in network.hosts():
        if str(host) not in usedIp: return str(host)

    print("Err!: Нету свободных IP-адресов!")
    return None

# Готово
def CreateAccount(dataDirectory, password):
    """
        Данная функция создает аккаунт для ноды.

            На вход передается путь для хранения данных об аккаунте и пароль. Пароль хранится в открытом виде.
        Функция сохраняет данные об аккаунте в переданном пути. Там же сохраняется пароль.

            На выходе функция возвращает адрес аккаунта, который является сгенерированным публичным ключом.
        В случае неудачи возвращается None.
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

    output = subprocess.run(commandsForCreate, capture_output=True, text=True)

    if output.returncode != 0:
        print("Err!: Не удалось создать аккаунт!")
        return None

    # Ищем ключ
    publicKey = re.search(r'0x[0-9a-fA-F]{40}', output.stdout)

    if publicKey:
        addr = publicKey.group(0)
        return addr
    
    return None # Не удалось создать аккаунт по другим причинам


# Готово
def CreateGenesisForClique(chainId, period, gasLimit, validatorAddr, balance, outputPath):
    """
        Данная функция создает genesis.json для Clique (PoA).

        Файл сохраняется в outputPath.
    """
    addressWithoutPrefix = validatorAddr

    if addressWithoutPrefix.startswith("0x"):
        addressWithoutPrefix = validatorAddr[2:]

    extradata = "0x" + "0" * 64 + addressWithoutPrefix + "0" * 130

    genesisFile = {
        "config": {
            "chainId": chainId,
            "clique": {
                "period": period,
                "epoch": 30000
            }
        },
        "difficulty": "1",
        "gasLimit": str(gasLimit),
        "extradata": extradata,
        "alloc": {
            validatorAddr: {"balance": str(balance)}
        }
    }

    with open(outputPath, "w") as f:
        json.dump(genesisFile, f, indent=2)


# Готово
def CheckGenesisFile(genesisPath):
    """
        Функция для проверки корректности genesis.json.

            Если в файле нету ошибок, то возвращаем название используемого алгоритма консенсуса.
        В случае неудачи возвращаем None и причину ошибки.

        На вход принимает путь, в котором лежит genesis.json.
    """
    if not genesisPath.exists():
        print("Err!: genesis.json не найден!")
        print("Попробуйте запустить DeleteAll.py и после InitializeNetwork.py")
        return None
    
    with open(genesisPath, "r") as jsonFile:
        genesisFile = json.load(jsonFile)

    genesisConfig = genesisFile.get("config")
    
    if not genesisConfig:
        print("Err!: genesis.json был создан не правильно!")
        return None
    
    chainId = genesisConfig.get("chainId")

    if chainId is None:
        print("Err!: genesis.json был создан не правильно!")
        print("Отсутсвует chainId!")
        return None
    
    print(f"Chain ID: {chainId}")

    if "clique" in genesisConfig:
        extradata = genesisFile.get("extradata")

        if (len(extradata) < 2 + 64 + 40 + 130):
            print("Err!: genesis.json был создан не правильно!")
            print("Отсутствует или неправильно был назначен валидатор")
            return None
        
        print("Найдена сеть с алгоритмом Clique")
        return "clique"
    
    else:
        print("Err!: genesis.json был создан не правильно!")
        print("Неизвестный алгоритм консенсуса или отсутствует его поддержка")
        return None


# Готово
def InitializeNode(dataDirectory):
    """
        Данная функция инициализирует ноду (создает БД с genesis.json).

        На вход подается путь, в котором будут сохранены файлы узла.

        Возращает true, если прошло успешно. False в случае ошибки.
    """
    genesisPath = CONFIG_DIR / "genesis.json"

    commands = [
        "docker", "run", "--rm",
        "-v", f"{CONFIG_DIR}:/config",
        "-v", f"{dataDirectory}:/data",
        DOCKER_IMAGE,
        "init", "--datadir", "/data",
        f"/config/{genesisPath.name}"
    ]

    output = subprocess.run(commands, capture_output=True, text=True)

    if output.returncode == 0:
        return True
    
    return False

# Готово
def StartValidatorNode(chainId, nodeName, httpPort, p2pPort, dataDir, addr, password):
    """
        Запускает ноду валидатора (с майнингом) с заранее известным Docker IP.

        Перед запуском контейнера определяем следующий свободный IP
        в Docker сети.

        Так enode с первого старта содержит правильный внутренний
        IP Docker сети, а не внешний IP хоста.
    """
    genesisPath = CONFIG_DIR / "genesis.json"
    containerName = f"geth-{nodeName}"

    # Определяем свободный IP заранее
    dockerIp = GetNextFreeIp()
    print(f"Назначаем Docker IP: {dockerIp}")

    RunCommands([
        "docker", "run", "-d",
        "--name", containerName,
        "--network", DOCKER_NETWORK,
        f"--ip={dockerIp}",
        "-p", f"{httpPort}:8545",
        "-p", f"{p2pPort}:30303",
        "-v", f"{genesisPath}:/config/genesis.json:ro",
        "-v", f"{dataDir}:/data",
        DOCKER_IMAGE,
        "--datadir=/data",
        "--ipcpath", "/data/geth.ipc",
        f"--networkid={chainId}",
        "--http",
        "--http.addr=0.0.0.0",
        "--http.port=8545",
        "--http.api=eth,net,web3,admin,miner,clique",
        "--http.corsdomain=*",
        "--allow-insecure-unlock",
        "--mine",
        f"--miner.etherbase={addr}",
        f"--unlock={addr}",
        "--password=/data/password.txt",
        "--nodiscover",
        f"--nat=extip:{dockerIp}",
    ])

    print(f"Нода-валидатор {nodeName} запущена на HTTP-порт {httpPort} и P2P-порт {p2pPort}!")



# Готово
def StartNode(nodeName, httpPort, p2pPort, dataDirectory):
    """
        Данная функция запускает ноду с выделенным свободным IP в Docker сети.
    """

    genesisPath = CONFIG_DIR / "genesis.json"
    chainId = GetNetworkId()
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

    print(f"Узел {nodeName} запущен на порту {httpPort} (не связанный)")


def GetNetworkId():
    """
        Данная функция ищет ID сети через genesis.json
    """
    genesisPath = CONFIG_DIR / "genesis.json"

    with open(genesisPath, "r") as jsonFile:
        genesisFile = json.load(jsonFile)

    chainId = genesisFile["config"]["chainId"]

    print(f"NetworkID: {chainId}")

    return chainId


def GetContainerDockerIp(containerName):
    """
        Получает внутренний IP контейнера в Docker сети.
        Именно этот IP должен быть в enode, чтобы контейнеры видели друг друга.
    """
    output = subprocess.run(
        [
            "docker", "inspect", "-f",
            "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            containerName
        ],
        capture_output=True, text=True
    )

    return output.stdout.strip()


def GetEnode(nodeName):
    """
        Данная функция получает Enode идентификатор ноды.
    """

    containerName = f"geth-{nodeName}"

    commandsForGet = [
        "docker", "exec", containerName,
        "geth", "--exec", "admin.nodeInfo.enode",
        "attach", "/data/geth.ipc"
    ]
    
    output = RunCommands(commandsForGet)

    if not output.stdout:
        return None

    lines = [line.strip() for line in output.stdout.splitlines() if line.strip()]
    
    if not lines:
        return None

    enode = lines[-1].strip('"')

    if not enode.startswith("enode://"):
        return None

    return enode


def AddPeer(nodeName, enode):
    """
        Данная функция подключает ноду у указанному enode.
    """

    containerName = f"geth-{nodeName}"

    commandsForAdd = [
        "docker", "exec", containerName,
        "geth", "--exec", f"admin.addPeer('{enode}')",
        "attach","/data/geth.ipc"
    ]

    output = RunCommands(commandsForAdd)

    if output and output.returncode == 0:
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


def DeleteContainers():
    """ Функция удаляет и останавливает контейнеры """
    
    commandsForFindContainers = [
        "docker", "ps", "-a", "--format", "{{.Names}}"
    ]
    
    output = subprocess.run(commandsForFindContainers, capture_output=True, text=True)

    containers = [name.strip() for name in output.stdout.splitlines() if name.strip().startswith("geth-")]

    if not containers:
        print("Нету контейнеров для удаления!")
        return


    count = 0
    for container in containers:
        if DeleteContainer(container.replace("geth-", "")):
            count += 1
    
    print(f"\nКоличество удаленных контейнеров: {count}")


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


def ShowNodeInfo(nodeName):
    if not CheckNode(nodeName):
        print("Узел на запущен!")
        return False
    

    container = f"geth-{nodeName}"

    ip = GetContainerDockerIp(container)

    print(f"IP-адрес -- {ip}")

    enode = GetEnode(nodeName)

    if enode:
        print(f"Enode -- {enode}")
    else:
        print("Не получилось получить Enode!")
        return False
    
    commandsForGetBlock = [
        "docker", "exec", container,
        "geth", "--exec", "eth.blockNumber",
        "attach", "/data/geth.ipc"
    ]

    output = subprocess.run(commandsForGetBlock, capture_output=True, text=True)

    if output.returncode == 0:
        print(f"Текущий блок: {output.stdout.strip()}")
    else:
        print("Не получилось найти информация о блоке!")
        return False
    
    commandsForGetPeers = [
        "docker", "exec", container,
        "geth", "--exec", "net.peerCount",
        "attach", "/data/geth.ipc"
    ]

    output = subprocess.run(commandsForGetPeers, capture_output=True, text=True)

    if output.returncode == 0:
        print(f"Пиры: {output.stdout.strip()}")
    else:
        print("Не получилось найти информацию о пирах!")
        return False

    return True
