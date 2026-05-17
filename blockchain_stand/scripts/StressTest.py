from ConnectNodes import *

def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)

    nodes = GetAllNodes()

    if len(nodes) < 2:
        print("Нужно минимум 2 узла!")
        sys.exit(1)
    
    print(f"Всего узлов: {len(nodes)}")

    for node in nodes:
        if IsValidator(node):
            print(f"{node} является валидатором!")
        else: print(f"{node} не валидатор!")
    
    try:
        transactionCount = int(input("Введите кол-во транзакций от каждого узла: "))
    except:
        transactionCount = 20

    print(f"\nКол-во транзакций от каждого узла: {transactionCount}")

    addresses = {}

    for node in nodes:
        address = GetNodeAddress(node)

        if address:
            addresses[node] = address
        else:
            print(f"Не удалось получить адрес {node}!")
            sys.exit(1)
        

    
    print("\n\nНачало стресс-теста:")

    total, success, fail = 0, 0, 0

    startTime = time.time()

    for node in nodes:
        print(f"Узел {node} отправляет {transactionCount} транзакций:")

        for i in range(transactionCount):
            targetsNode = [n for n in nodes if n != node]
            target = random.choice(targetsNode)
            address = addresses[target]

            weiToTransmit = random.uniform(5000, 100000)

            res, txHash = SendTransaction(node, address, weiToTransmit)
            total += 1

            if res:
                success += 1
                print(f"{node} -> {target} отправлено {weiToTransmit}")
            else:
                fail += 1
                print(f"{node} -> {target} отправлено {weiToTransmit}")
        
            time.sleep(3)
        
    totalTime = time.time() - startTime

    print("\n\nРезультаты:")

    print(f"Успешных транзакций: {success}")
    print(f"Неуспешных транзакций: {fail}")
    print(f"Всего: {total}")
    print(f"Потраченное время: {totalTime:.1f} сек")


    print("\n\nБалансы узлов:")

    for node in nodes:
        balance = GetBalance(node)
        if balance:
            print(f"   {node}: {balance} wei")


if __name__ == "__main__":
    main()