generate multiply(a, b)
generate power(base, exp)

play() {
    result: power(2, 4)
    shootNxt("2 raised to the power of 4 is {result}")
}

generate power(base, exp) {
    if exp == 0 {
        recall 1
    } else {
        recall multiply(base, power(base, exp - 1))
    }
}

generate multiply(a, b) {
    recall a * b
}

gameOver