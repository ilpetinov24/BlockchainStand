// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vulnerable {
    // Данные
    mapping(address => uint256) public balances;
    uint256 public totalBalance;

    event Deposit(address indexed user, uint256 txValue);
    event Withdraw(address indexed user, uint256 txValue);

    // Функция, которая принимает eth и добавляет к балансу пользователя
    function deposit() external payable {
        require(msg.value > 0, "Cannot deposit 0");
        balances[msg.sender] += msg.value;
        totalBalance += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    // Уязвимая ф-ия. Сначала отправляет eth, а потом обновляет
    function withdraw(uint256 txValue) external {
        require(balances[msg.sender] >= txValue, "Insufficient balance");
        require(totalBalance >= txValue, "Vault has insufficient funds");
        
        // Сначала отправляем
        (bool success, ) = msg.sender.call{value: txValue}("");
        require(success, "Transfer failed");
        
        // Потом обновляем
        balances[msg.sender] -= txValue;
        totalBalance -= txValue;
        
        emit Withdraw(msg.sender, txValue);
    }

    // Безопасная версия прошлой функции
    function withdrawSafe(uint256 txValue) external {
        require(balances[msg.sender] >= txValue, "Insufficient balance");
        require(totalBalance >= txValue, "Vault has insufficient funds");
        
        // Сначала обновляем
        balances[msg.sender] -= txValue;
        totalBalance -= txValue;
        
        // Потом отправляем
        (bool success, ) = msg.sender.call{value: txValue}("");
        require(success, "Transfer failed");
        
        emit Withdraw(msg.sender, txValue);
    }

    // Получить баланс контракта
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }

    // Получить баланс пользователя
    function getUserBalance(address user) external view returns (uint256) {
        return balances[user];
    }

}