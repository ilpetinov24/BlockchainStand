from Functions import *


def main():
    if not CheckDockerRun():
        print("Docker не запущен!")
        sys.exit(1)
        
    if not CheckDockerNetwork():
        print(f"Err!: Docker-сеть {DOCKER_NETWORK} не найдена!")
        sys.exit(1)
    else: print(f"Docker-сеть {DOCKER_NETWORK} существует!")

    ShowNetworkInfo()


if __name__ == "__main__":
    main()


