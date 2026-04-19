from Functions import *


def main():
    if not CheckDockerRun():
        print("Err!: Docker не запущен!")
        sys.exit(1)

    if len(sys.argv) < 5:
        print("Err!: Недостаточно аргументов")
        print("Пример: CreateNewNode.py <node_name> <http-порт> <p2p-порт> <пароль>")
        sys.exit(1)

    nodeName = sys.argv[1]
    httpPort = sys.argv[2]
    p2pPort = sys.argv[3]
    password = sys.argv[4]

    genesisPath = CONFIG_DIR / "genesis.json"

    dataDir = BASE_DIR / "nodes" / nodeName / "data"

    if not CheckDockerNetwork():
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        sys.exit(1)
    else: print(f"Docker-сеть {DOCKER_NETWORK} существует!")
    
    print()

    print("Проверка genesis.json:")
    check = CheckGenesisFile(genesisPath)

    if check: print("Успешно!")
    else:
        print("Err!: genesis.json не прошел проверку!")
        sys.exit(1)
    
    print()

    print("Создание узла с следующими параметрами:")
    print(f"    HTTP: {httpPort}")
    print(f"    P2P: {p2pPort}\n\n")

    print("1. Создание аккаунта:")
    address = CreateAccount(dataDir, password)

    if not address:
        print("Err!: Не удалось создать аккаунт")
        sys.exit(1)
    else: print(f"Создан аккаунт: {address}")
    
    print()

    print("\n2. Инициализация узла:")
    check = InitializeNode(dataDir)

    if check:
        print("Успешно!")
    else:
        print("Err!: Не получилось инициализировать узел!")
        sys.exit(1)

    print("\n3. Запуск:")
    StartNode(nodeName, httpPort, p2pPort, dataDir)

    print("\nУзел запущен:")
    print(f"Данные: {dataDir}")
    print(f"Адрес: {address}")
    print(f"Пароль: {password}")
    print(f"HTTP: http://localhost:{httpPort}")


if __name__ == "__main__":
    main()