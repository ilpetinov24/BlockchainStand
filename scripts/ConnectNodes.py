#!/usr/bin/env python3

"""
    Данный скрипт соединяет две ноды между собой.

    Для соединения обязательно, чтобы ноды были созданы и находились в одной сети.
"""

CONFIG_DIR = Path.home() / "blockchain_stand" / "config"


def CheckDockerRun():
    """
        Функция для проверки Docker. Проверяет запущен ли он или нет.
    """
    commandForCheck = ["docker", "info"]

    output = subprocess.run(commandForCheck, capture_output=True)

    if output.returncode == 0:
        return True
    
    return False


def RunCommands(commands):
    """Данная функция запускает команды в CLI."""
    output = subprocess.run(commands, capture_output=True, text=True)

    if output.returncode != 0:
        print(f"Error!: {output.stderr}")
        sys.exit(1)
    
    return output


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


def CheckNode(nodeName):
    """
        Данная функция проверяет, что нода существует и запущена.
    """

    commandsForCheck = [
        "docker", "ps", "-q", "-f", f"name=geth-{nodeName}"
    ]

    output = subprocess.run(commandsForCheck, capture_output=True, text=True)

    if output.stdout.strip():
        return True
    
    return False


def main():
    if len(sys.argv) < 3:
        print("Err!: Недостаточно аргументов")
        print("Пример: ConnectNodes.py <node_name1> <node_name2>")
        sys.exit(1)
    
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)
    
    firstNode = sys.argv[1]
    secondNode = sys.argv[2]

    if not CheckNode(firstNode):
        print(f"Err!: {firstNode} не запущена")
        sys.exit(1)
    
    if not CheckNode(secondNode):
        print(f"Err!: {secondNode} не запущена")
        sys.exit(1)
    

    print(f"Получаем enode ноды {secondNode}:")
    
    enodeSecondNode = GetEnode(secondNode)

    if not enodeSecondNode:
        print(f"Не получилось получить enode ноды {secondNode}")
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