play(){
	hp i
    is_palin: true
	string: load("Enter a string: ")
    last_digit: rounds(string)
    if last_digit % 2 == 0 {
    	is_palin: false
    } else {
      for i: 0, i < toHp(last_digit/2) + 1, i += 1 {
          if string[i] == string[last_digit-1] {
              resume
          } else {
              is_palin: false
              checkpoint
          }
          last_digit -= 1
      }
    }
    if is_palin {
    	shoot("\nString '{string}' is a palindrome.")
	} else {
    	shoot("\nString '{string}' is not a palindrome.")
    }
}

gameOver