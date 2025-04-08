# Activity - Number 5 
generate input_numbers()
generate multiply(num1, num2)
generate divide(num1, num2)
generate add(num1, num2)
generate subtract(num1, num2)

play(){
  hp num1, num2
  
  shootNxt("Choose an operation:")
  shootNxt("[1] Multiplication [2] Division [3] Addition [4] Subtraction")
  operation: loadNum("Enter your choice: ")
  flank operation {
  	choice 1:
    	num1, num2: input_numbers()
    	multiply(num1, num2)
    choice 2:
    	num1, num2: input_numbers()
    	divide(num1, num2)
    choice 3:
    	num1, num2: input_numbers()
    	add(num1, num2)
    choice 4:
    	num1, num2: input_numbers()
    	subtract(num1, num2)
    backup:
    	shoot("\nInvalid Choice!")
  }  
}

generate input_numbers() {
	hp num1, num2
	num1: loadNum("\nEnter first integer: ")
    num2: loadNum("\nEnter second integer: ")
    recall num1, num2
}

generate multiply(num1, num2) {
    product: num1 * num2
    shoot("\nThe product of {num1} and {num2} is {product}.")
}

generate divide(num1, num2) {
    quotient: num1 / num2
    shoot("\nThe quotient of {num1} and {num2} is {quotient.2f}.")
}

generate add(num1, num2) {
    sum: num1 + num2
    shoot("\nThe sum of {num1} and {num2} is {sum}.")
}

generate subtract(num1, num2) {
    difference: num1 - num2
    shoot("\nThe difference of {num1} and {num2} is {difference}.")
}

gameOver