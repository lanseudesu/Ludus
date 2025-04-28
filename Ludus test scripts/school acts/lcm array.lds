#Activity - LCM array

generate get_lcm(array)

play(){
 hp max, lcm, n1, n2
 arr[]: [4,6,7,9,12,16]
 lcm: get_lcm(arr)
 
 shoot(lcm)
}

generate get_lcm(array) {
	hp i
    lcm: array[1]
    for i: 0, i < rounds(array), i += 1 {
    	if i == rounds(array) - 1 {
        	checkpoint
        }
    	num1: lcm
        num2: array[i + 1]

        while num2 != 0 {
            temp: num2
            num2: num1 % num2
            num1: temp
        }
        lcm: toHp((lcm * array[i + 1]) / num1)
    }
    recall lcm
    
    
}
gameOver