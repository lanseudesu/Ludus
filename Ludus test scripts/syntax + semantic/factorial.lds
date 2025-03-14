generate factorial(n)

play() {
    result: factorial(5)
    shootNxt("The factorial of 5 is: {result}")
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