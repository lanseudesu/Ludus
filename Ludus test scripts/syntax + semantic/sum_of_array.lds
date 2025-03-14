numbers[]: [1.1, 2.2, 3.3, 4.4]

generate sum_array(arr)

play() {
    total: sum_array(numbers)
    shootNxt("The total sum is: {total}.")
}

generate sum_array(arr) {
    xp total
    hp i
    for i: 0, i < rounds(arr), i += 1 {
        total += arr[i]
    }
    recall total
}

gameOver