numbers[]: [1, 2, 3, 4, 5]

generate reverse_array(arr) 

play() {
    numbers : reverse_array(numbers)
}

generate reverse_array(arr) {
    hp i
    hp new_arr[]
    for i: rounds(arr) - 1, i >= 0, i -= 1 {
        new_arr.join(arr[i])
    }
    recall new_arr
}

gameOver