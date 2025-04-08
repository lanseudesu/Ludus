generate factorial(n)

play() {
	num: loadNum("Enter number: ")
    result: factorial(num)
    shoot("\nThe factorial of {num} is: {result}")
}

generate factorial(n) {
    fact: 1
    hp i
    for i: 1, i <= n, i += 1 {
        fact *= i
    }
    recall fact
}

gameOver