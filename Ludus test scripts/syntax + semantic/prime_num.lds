generate check_prime(n)

play() {
    check_prime(7)
    check_prime(11)
}

generate check_prime(n) {
    is_prime: true
    hp i
    if n <= 1 {
        is_prime: false
    } else {
    	num: n / 2
        for i: 2, i <= toHp(num), i += 1 {
            if n % i == 0 {
                is_prime: false
                checkpoint
            }
        }
    }

    if is_prime {
        shootNxt("{n} is a prime number.")
    } else {
        shootNxt("{n} is not a prime number.")
    }
}

gameOver