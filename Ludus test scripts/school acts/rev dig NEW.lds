play() {
	hp input, i
    flag neg
    input: loadNum("Insert an integer: ")
    shootNxt()
    temp_str: toComms(input)
    if temp_str[0] == "-" {
    	neg: true
        temp_str.drop(0)
    }
    new_str: ""
    for i: rounds(temp_str) - 1, i >= 0, i -= 1{
    	new_str.join(temp_str[i])
    }
    if neg {
    	shoot("-{new_str}")
    } else {
    	shoot(new_str)
    }
}

gameOver