numbers[]: [1, 2, 3, 4, 5]

generate reverse_array(arr) 

play() {
	shootNxt("original array:")
	hp i
	for i: 0, i < rounds(numbers), i += 1 {
    	if i == 4 {
        	shoot("{numbers[i]}")
        } else {
        	shoot("{numbers[i]}, ")
        }
    }
    
    numbers : reverse_array(numbers)
    shootNxt("\nreversed array:")
    for i: 0, i < rounds(numbers), i += 1 {
    	if i == 4 {
        	shoot("{numbers[i]}")
        } else {
        	shoot("{numbers[i]}, ")
        }
    }
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