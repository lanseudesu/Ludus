#Activity - Number 20

play() {
    year: loadNum("Enter Year: ")
    
    if year % 400 == 0 || (year % 4 == 0 && year % 100 != 0) {
    	shoot("\n\n{year} is a leap year.")
    } else {
    	shoot("\n\n{year} is not a leap year.")
	}
    
}

gameOver
