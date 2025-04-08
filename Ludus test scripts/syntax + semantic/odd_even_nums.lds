numbers[]: [1, 2, 3, 4, 5, 6, 7, 8, 9]

generate count_even_odd(arr) 

play() {
    count_even_odd(numbers)
}

generate count_even_odd(arr) {
    hp even_count
    hp odd_count
    hp i

    for i: 0, i < rounds(arr), i += 1 {
        if arr[i] % 2 == 0 {
            even_count += 1
        } else {
            odd_count += 1
        }
    }

    shootNxt("Even numbers: {even_count}")
    shootNxt("Odd numbers: {odd_count}")
}

gameOver