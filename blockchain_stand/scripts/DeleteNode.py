from Functions import *


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)

    if len(sys.argv) < 1:
        print("Err!: Недостаточно аргументов!")
        print("Пример: DeleteNode.py <nodeName>")
        sys.exit(1)

    if not CheckDockerNetwork():
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        sys.exit(1)
    else: print(f"Docker-сеть {DOCKER_NETWORK} существует!")
    
    print()

    print("1. Остановка и удаление контейнер:")
    
    DeleteContainer(sys.argv[1])

    print("\n2. Удаление данных:")

    DeleteNodeData(sys.argv[1])


if __name__ == "__main__":
    main()
