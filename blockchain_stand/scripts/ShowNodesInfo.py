from Functions import *


def GetNodes():
    nodes = []

    commandsForGet = [
        "docker", "ps", "--filter", "name=geth-",
        "--format", "{{.Names}}"
    ]

    output = subprocess.run(commandsForGet, capture_output=True, text=True)

    if not output.stdout.strip():
        return nodes

    for container in output.stdout.strip().split("\n"):
        if container:
            nodes.append(container.replace("geth-", ""))
    
    return nodes


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)

    if not CheckDockerNetwork():
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        sys.exit(1)
    else: print(f"Docker-сеть {DOCKER_NETWORK} существует!")


    nodes = GetNodes()

    for node in nodes:
        print(f"\nИнформация о узле {node}")

        if ShowNodeInfo(node):
            print("Успешно!\n")
        else:
            print("Ошибка!\n")


if __name__ == "__main__":
    main()
