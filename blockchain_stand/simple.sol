pragma solidity ^0.8.0;

contract Counter {
    // Данные
    uint256 public count;

    function increment() external {
        count += 1;
    }

    function decrement() external {
        require(count > 0, "Не может быть < 0");
        count -= 1;
    }

    function getCount() external view returns (uint256) {
        return count;
    }

}