from Functions import *
import time

def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    firstNodeDir = BASE_DIR / "nodes" / "validator_node" / "data"

    consensus = sys.argv[1].lower()

    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)


    if len(sys.argv) != 5:
        print("Err!: Недостаточно аргументов")
        print("Use: clique <chainId> <period> <gasLimit>")
        sys.exit(1)
           
    chainId = int(sys.argv[2])
    period = int(sys.argv[3])
    gasLimit = int(sys.argv[4])
    
    try:
        validatorsCount = int(input("\nВведите кол-во валидаторов (>=1):"))

        if validatorsCount < 1:
            print("Err!: Кол-во валидаторов должно быть >= 1")
            sys.exit(1)
    except ValueError:
        print("Err!: Введите число!")
        sys.exit(1)
    
    print(f"Создание Docker-сети {DOCKER_NETWORK}")
    check = CreateDockerNetwork()

    if not check:
        print(f"Err!: Не получилось создать Docker-сеть {DOCKER_NETWORK}!\n")
        sys.exit(1)
    else: print("Успешно!\n")

    validators = []

    print("Ввод данных для валидаторов:\n")

    for i in range(validatorsCount):
        nodeName = f"validator_node{i+1}"

        password = input(f"Введите пароль для {nodeName}:").strip()
        while not password:
            print("Пароль должен быть не пустым!\n")
            password = input(f"Введите пароль для {nodeName}:").strip()


        balance = int(input(f"Введите баланс для {nodeName} в wei: "))

        
        httpPort = input(f"Введите http-порт для {nodeName} (по умолчанию 8545 + i)")
        if not httpPort:
            httpPort = 8545 + i
        else:
            httpPort = int(httpPort)

        p2pPort = input(f"Введите p2p-порт для {nodeName} (по умолчанию 30303 + i)")
        if not p2pPort:
            p2pPort = 30303 + i
        else:
            p2pPort = int(httpPort)

        nodeDirectory = BASE_DIR / "nodes" / nodeName / "data"
        nodeDirectory.mkdir(parents=True, exist_ok=True)

        print(f"\nСоздаем аккаунт для {nodeName}:")
        address = CreateAccount(nodeDirectory, password)

        if not address:
            print(f"Err!: Не удалось создать аккаунт для {nodeName}!")
            sys.exit(1)
        
        print(f"Аккаунт создан: {address}")

        validators.append({
            "name": nodeName,
            "address": address,
            "dataDir": nodeDirectory,
            "password": password,
            "balance": balance,
            "httpPort": httpPort,
            "p2pPort": p2pPort
        })

        print()
    


    print("\n\nСоздание genesis.json для Clique (PoA):")
    genesisPath = CONFIG_DIR / "genesis.json"
        
    validatorAdrresses = [v["address"] for v in validators]
    validatorsBalance = [v["balance"] for v in validators] 

    CreateGenesisForClique(
        chainId, period, gasLimit, validatorAdrresses,
        validatorsBalance, genesisPath
    )

    print("Файл genesis.json создан (Clique)")
    print(f"    chainId: {chainId}")
    print(f"    period: {period} секунд")
    print(f"    gasLimit: {gasLimit} wei or {gasLimit / 10**18} eth")

    i = 0
    for balance in validatorsBalance:
        print(f"    geth-validator_node{i + 1} balance: {balance} wei or {balance / 10**18} eth")
        i += 1

    print(f"    validator: {validatorAdrresses}")


    print("\nЗапуск и инициализация всех валидаторов:")

    for validator in validators:
        print(f"\n  Запуск {validator['name']}...")

        if not InitializeNode(validator['dataDir']):
            print(f"    Err!: Не удалось инициализировать {validator['name']}!")
            sys.exit(1)
        
        StartValidatorNode(chainId, validator['name'],
                           validator['httpPort'], validator['p2pPort'],
                           validator['dataDir'], validator["address"],
                           validator["password"])
        
        time.sleep(2)

    print("Успешно!")


if __name__ == "__main__":
    main()