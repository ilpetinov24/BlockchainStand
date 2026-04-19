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


def CreateDockerNetwork():
    """
        Создаёт Docker сеть для узлов, если она ещё не была создана.
    """
    
    # Команда выводит только ID сети
    commandsForCheck = [
        "docker", "network", "ls", 
        "-q", "-f", f"name={DOCKER_NETWORK}"
    ]

    commandsForCreate = ["docker", "network", "create", DOCKER_NETWORK]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    # Проверяем есть ли ID
    if not output.stdout.strip():
        subprocess.run(commandsForCreate, check=True)
        return True

    return False


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
         "-f", "{{json .}}"],
        capture_output=True, text=True
    )

    if output.returncode != 0:
        print("Err!: Не удалось получить информацию о Docker сети!")
        sys.exit(1)

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
        sys.exit(1)
    
    for container in networkInfo.get("Containers", {}).values():
        ip = container.get("IPv4Address", "").split("/")[0] # Маска нам не нужна
        if ip: usedIp.add(ip)

    # Возвращаем первый свободный IP.
    hosts = list(network.hosts())
    for host in hosts:
        if str(host) not in usedIp:
            return str(host)

    print("Err!: Нет свободных IP в Docker сети!")
    sys.exit(1)


def CreateAccountForValidator(dataDirectory, password):
    """
        Данная функция создает аккаунт для валидатора.

        Нужна для того, чтобы создать genesis.json для Clique (PoA).
        Файл genesis.json сразу требует указания валидатора в сети.
    """

    # Создаем каталог для хранения данных о аккаунте
    dataDirectory.mkdir(parents=True, exist_ok=True) 

    passwordFile = dataDirectory / "password.txt"
    passwordFile.write_text(password)

    # Запускаем geth, чтобы создать аккаунта
    # После завершения работы контейнер удаляется, но данные о аккаунте сохраняются
    commandsForCreate = [
        "docker", "run", "--rm",
        "-v", f"{dataDirectory}:/data",
        DOCKER_IMAGE,
        "account", "new", "--datadir",
        "/data", "--password", "/data/password.txt"
    ]

    output = RunCommands(commandsForCreate)

    # Ищем ключ
    publicKey = re.search(r'0x[0-9a-fA-F]{40}', output.stdout)

    if publicKey:
        addr = publicKey.group(0)
        return addr

    return None


def CreateGenesisForClique(chainId, period, gasLimit, validatorAddr, balance, outputPath):
    """
        Данная функция создает genesis.json для Clique (PoA)
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



def InitBlock(dataDirectory):
    """
        Данная функция создает первый блок (создает БД с genesis.json)
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

    RunCommands(commands)



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

    print(f"Нода-валидатор {nodeName} запущена на порту {httpPort}!")


def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    firstNodeDir = BASE_DIR / "nodes" / "validator_node" / "data"

    consensus = sys.argv[1].lower()

    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)

    if consensus == "clique":
        if len(sys.argv) != 7:
            print("Err!: Недостаточно аргументов")
            print("Use: clique <chainId> <period> <gasLimit> <balance> <passwordForValidatorAccount>")
            sys.exit(1)
        
        print(f"Создание Docker-сети {DOCKER_NETWORK}:")
        check = CreateDockerNetwork()

        if check: print(f"\nDocker-сеть {DOCKER_NETWORK} создана!")
        else: print(f"\nDocker-сеть {DOCKER_NETWORK} уже существует!")
         
        chainId = int(sys.argv[2])
        period = int(sys.argv[3])
        gasLimit = int(sys.argv[4])
        balance = int(sys.argv[5])
        password = sys.argv[6]

        print("\nСоздание аккаунта для валидатора:")
        validatorAddress = CreateAccountForValidator(firstNodeDir, password)

        if not validatorAddress:
            print("Err!: Не удалось создать аккаунт")
            sys.exit(1)
        else: print(f"Создан аккаунт: {validatorAddress}")

        print("\nСоздание genesis.json для Clique (PoA):")
        genesisPath = CONFIG_DIR / "genesis.json"
        
        CreateGenesisForClique(
            chainId, period, gasLimit, validatorAddress,
            balance, genesisPath
        )

        print("Файл genesis.json создан (Clique)")
        print(f"    chainId: {chainId}")
        print(f"    period: {period} секунд")
        print(f"    gasLimit: {gasLimit} wei or {gasLimit / 10**18} eth")
        print(f"    balance: {balance} wei or {balance / 10**18} eth")
        print(f"    validator: {validatorAddress}")

        print("\nСоздание Genesis-блока:")
        InitBlock(firstNodeDir)
        print("Genesis-блок создан, база данных инициализирована!")

        print("\nЗапуск ноды-валидатора:")
        StartValidatorNode(chainId, "validator_node", 8545, 30303, firstNodeDir, validatorAddress, password)
        print()

    else:
        print("Err!: Используйте clique!")
        sys.exit(1)


if __name__ == "__main__":
    main()