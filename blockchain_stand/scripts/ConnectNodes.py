from Functions import *


def main():
    if len(sys.argv) < 3:
        print("Err!: Недостаточно аргументов")
        print("Пример: ConnectNodes.py <nodeName1> <nodeName2>")
        sys.exit(1)
    
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)
    
    check = CheckDockerNetwork()

    if not check:
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        sys.exit(1)
    else: print(f"Docker-сеть {DOCKER_NETWORK} существует!")
    print()

    firstNode = sys.argv[1]
    secondNode = sys.argv[2]

    if GetContainerDockerIp(firstNode) != GetContainerDockerIp(secondNode):
        print("Err!: Узлы находятся в разных сетях!")
        sys.exit(1)

    if not CheckNode(firstNode):
        print(f"Err!: {firstNode} не запущена")
        sys.exit(1)
    
    if not CheckNode(secondNode):
        print(f"Err!: {secondNode} не запущена")
        sys.exit(1)
    

    print(f"Получаем enode ноды {secondNode}:")
    
    enodeSecondNode = GetEnode(secondNode)

    if not enodeSecondNode:
        print(f"Не получилось получить enode-идентификатор узла {secondNode}")
        sys.exit(1)
    
    print(f"Enode: {enodeSecondNode}")

    print(f"\nПодключаем {firstNode} к {secondNode}")

    if AddPeer(firstNode, enodeSecondNode):
        print("Успешно!")
    else:
        print("Err!: Подключиться не удалось!")
        sys.exit(1)
    

if __name__ == "__main__":
    main()