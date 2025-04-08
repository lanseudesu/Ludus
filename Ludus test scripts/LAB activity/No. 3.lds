# Activity - Number 3 (Addition)

play() {
	hp num1, num2
	num1: loadNum("Enter first integer: ")
    shootNxt()
    num2: loadNum("Enter second integer: ")
    
    sum: num1 + num2
    shootNxt()
    shoot("The sum of {num1} and {num2} is {sum}.")
}

gameOver