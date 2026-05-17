from Functions import *
from decimal import Decimal

def main():
    """
        Скрипт будет брать половину баланса главного валидатор и
        распределять между всем обычными узлами.
    """
    mainValidatorInfo = GetMainValidatorInfo()
    validatorBalance = GetBalance(mainValidatorInfo["name"]).strip('"')

    if not validatorBalance:
        print("Не удалось получить баланс главного валидатора!")
        sys.exit(1)
    
    nodes = GetNodes()

    if not nodes:
        print("Нету узлов для распределения монет!")
        sys.exit(1)
    
    print(f"Найдено узлов: {len(nodes)}")

    balanceForDistribute = int(Decimal(validatorBalance)) // 2
    
    balanceForEachNode = balanceForDistribute // len(nodes)

    if balanceForEachNode <= 0:
        print("Мало баланса для распределения!")
        sys.exit(1)
    
    print("\nРаспределение монет:\n")
    for node in nodes:
        if SendMoney(node, balanceForEachNode):
            print("Успешно!")
        else:
            print("Ошибка!")


    print("\n\nПодождите 30 секунд!")
    time.sleep(30)


    print("\nБаланс валидатора: ")
    print(GetBalance(mainValidatorInfo["name"]))

    print("\nОбычные узлы:")
    for node in nodes:
        balance = GetBalance(node)
        if balance:
            print(f"  {node}: {balance} wei")



if __name__ == "__main__":
    main()