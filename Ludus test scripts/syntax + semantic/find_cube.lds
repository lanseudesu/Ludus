a: 3
generate find_cube(n)
generate is_even(y)

play(){
	number: loadNum("Enter a number: ")
	find_cube(number)
}

generate find_cube(n){
	hp i
    for i: 1, i <= n, i += 1{
        cube: i^3
        is_cube_even: is_even(cube)
    	shootNxt("\nThe cube of {i} is equals to: {cube}.")
        if is_cube_even{
    		shootNxt("{cube} is an even number.")
        } else {
        	shootNxt("{cube} is an odd number.")
        }
    }
    
}

generate is_even(y){
	result: y % 2 == 0
    recall result
}

gameOver