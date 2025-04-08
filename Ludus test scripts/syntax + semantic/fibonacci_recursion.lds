generate fibonacci(n)

play() {
    n: loadNum("Enter a number: ")
    result: fibonacci(n)
    shootNxt("\nThe {n}th Fibonacci number is {result}")
}

generate fibonacci(n) {
    if n == 0 {
        recall 0
    } elif n == 1 {
        recall 1
    } else {
        recall fibonacci(n - 1) + fibonacci(n - 2)
    }
}

gameOver