from Functions import *


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
        
        print(f"1. Создание Docker-сети {DOCKER_NETWORK}")
        check = CreateDockerNetwork()

        if not check:
            print(f"Err!: Не получилось создать Docker-сеть {DOCKER_NETWORK}!")
            sys.exit(1)
        else: print("Успешно!")
         
        chainId = int(sys.argv[2])
        period = int(sys.argv[3])
        gasLimit = int(sys.argv[4])
        balance = int(sys.argv[5])
        password = sys.argv[6]

        print("\n2. Создание аккаунта для валидатора")
        validatorAddress = CreateAccount(firstNodeDir, password)

        if not validatorAddress:
            print("Err!: Не удалось создать аккаунт")
            sys.exit(1)
        else: print(f"Создан аккаунт: {validatorAddress}")

        print("\n3. Создание genesis.json для Clique (PoA):")
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

        print("\n4. Создание Genesis-блока:")
        InitializeNode(firstNodeDir)
        print("Genesis-блок создан, база данных инициализирована!")

        print("\n5. Запуск ноды-валидатора:")
        StartValidatorNode(chainId, "validator_node", 8545, 30303, firstNodeDir, validatorAddress, password)
        print()

    else:
        print("Err!: Используйте clique!")
        sys.exit(1)


if __name__ == "__main__":
    main()