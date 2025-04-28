#Activity - permutation
generate permu(char_first, str)

play(){
   input: load("Enter a string: ")
   shootNxt()
   permu("", input)
}

generate permu(char_first, str){	
	if rounds(str) == 0 {
    	shootNxt(char_first)
		recall void
    }
    hp i
    for i:0, i< rounds(str), i+=1{
    	temp_str: str
        curr_char: str[i] 
        temp_str.drop(i) 
        remaining_char: temp_str 
        permu(char_first + curr_char, remaining_char)
    }
	
}

gameOver