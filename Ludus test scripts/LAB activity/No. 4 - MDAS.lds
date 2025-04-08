#Activity - 4 (MDAS)


play() {

	num1: loadNum("Enter first number: ")
    num2: loadNum("\nEnter second number: ")
   	shootNxt()
    
    result: (num1 + num2) * num2 - num1 / num2
    
    shootNxt("\nThe result of the equation is {result.2f}.")

}
gameOver
