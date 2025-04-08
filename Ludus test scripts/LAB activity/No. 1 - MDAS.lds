# Activity - Number 1

play() {
	hp num1, num2
	num1: loadNum("Enter first integer: ")
    shootNxt()
    num2: loadNum("Enter second integer: ")
    
    result: num1 / (num2 - (num1 + num2 * num1))
    shootNxt()
    shoot(result.2f)
}

gameOver