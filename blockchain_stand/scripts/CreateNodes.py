from Functions import *
import time


def main():
    if not CheckDockerRun():
        print("Err!: Docker не запущен!")
        sys.exit(1)

    if len(sys.argv) < 4:
        print("Err!: Недостаточно аргументов")
        print("For example: CreateMultipleNodes.py <startHttpPort> <startP2pPort> <count>")
        sys.exit(1)

    startHttpPort = int(sys.argv[1])
    startP2pPort = int(sys.argv[2])
    count = int(sys.argv[3])

    if count < 1:
        print("Err!: Количество узлов должно быть >= 1!")
        sys.exit(1)

    genesisPath = CONFIG_DIR / "genesis.json"

    if not CheckDockerNetwork():
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        print("Сначала запустите InitializeNetwork.py")
        sys.exit(1)
    else:
        print(f"Docker-сеть {DOCKER_NETWORK} существует!")
    
    print()

    print("Проверка genesis.json:")
    check = CheckGenesisFile(genesisPath)

    if check: print("Успешно!")
    else:
        print("Err!: genesis.json неправильный!")
        sys.exit(1)
    
    print(f"\nСоздание {count} узлов\n")

    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=geth-", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    nodes = []
    for container in result.stdout.strip().split("\n"):
        if container:
            nodeName = container.replace("geth-", "")
            nodes.append(nodeName)
    
    newNodes = []
    nextHttpPort = startHttpPort
    nextP2pPort = startP2pPort

    for i in range(count):
        nodeName = input("Введите имя для узла: ")
        
        while nodeName in nodes:
            print("Имя уже занято!\n")
            nodeName = input("Введите имя для узла: ")
        
        httpPort = nextHttpPort + i + 1
        p2pPort = nextP2pPort + i + 1
        
        print(f"\n  Узел {i+1}: {nodeName}")
        print(f"    HTTP порт: {httpPort}")
        print(f"    P2P порт: {p2pPort}")
        
        password = input(f"Введите пароль для {nodeName}: ")
        
        while not password:
            print("Пароль не может быть пустым!\n")
            password = input(f"Введите пароль для {nodeName}: ")
        
        dataDir = BASE_DIR / "nodes" / nodeName / "data"
        
        print("\nСоздание аккаунта:")
        address = CreateAccount(dataDir, password)
        
        if not address:
            print(f"Err!: Не удалось создать аккаунт для {nodeName}!")
            sys.exit(1)
        else: print(f"   Создан аккаунт: {address}")
        
        print("\nИнициализация узла:")

        if not InitializeNode(dataDir):
            print(f"Err!: Не получилось инициализировать узел {nodeName}!")
            sys.exit(1)
        print("   Успешно!")
        
        print("\nЗапуск узла:")
        StartNode(nodeName, httpPort, p2pPort, dataDir)
        
        newNodes.append({
            "name": nodeName,
            "address": address,
            "httpPort": httpPort,
            "p2pPort": p2pPort,
            "password": password,
            "dataDir": dataDir
        })
        
        print(f"\n  Узел {nodeName} создан!")
        print(f"    Адрес: {address}")
        print(f"    HTTP: http://localhost:{httpPort}")
        
        time.sleep(2)
    
    print(f"\nСоздано узлов: {len(newNodes)}\n")
    
    

    print("\nСозданные узлы:")
    for node in newNodes:
        print(f"   {node['name']}: http://localhost:{node['httpPort']} (адрес: {node['address']})")


if __name__ == "__main__":
    main()