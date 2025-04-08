#Activity - 4 (Subtraction)


play() {

	num1: loadNum("Enter first number: ")
    num2: loadNum("\nEnter second number: ")
   	shootNxt()
    
    diff: num1 - num2
    
    shootNxt("The difference of {num1} minus {num2} is {diff}.")

}
gameOver
