generate check_armstrong(n)
generate count_digits(n) 

play() {
    num: loadNum("Enter a number: ")
    is_armstrong: check_armstrong(num)

    if is_armstrong {
        shootNxt("\n{num} is an Armstrong number.")
    } else {
        shootNxt("\n{num} is not an Armstrong number.")
    }
}

generate check_armstrong(n) {
    original: n
    hp sum
    digits: count_digits(n)

    while n > 0 {
        last_digit: n % 10
        sum += last_digit^digits
        x: n/10
        n: toHp(x)
    }

    recall sum == original
}

generate count_digits(n) {
    hp count
    while n > 0 {
        x: n/10
        n: toHp(x)
        count += 1
    }
    recall count
}

gameOver
