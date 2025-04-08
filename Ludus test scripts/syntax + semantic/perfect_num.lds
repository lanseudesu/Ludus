generate check_perfect(n)

play() {
    num: loadNum("Enter a number: ")
    is_perfect: check_perfect(num)

    if is_perfect {
        shootNxt("\n{num} is a Perfect number.")
    } else {
        shootNxt("\n{num} is not a Perfect number.")
    }
}

generate check_perfect(n) {
    hp sum, i
    for i: 1, i < n, i += 1 {
        if n % i == 0 {
            sum += i
        }
    }

    recall sum == n
}

gameOver