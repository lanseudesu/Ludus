# Activity - Number 2
play(){
	hp val1, val2
    
    val1: loadNum("Enter the First Integer: ")
    shootNxt()
    val2: loadNum("Enter the Second Integer: ")
    
    result: ((val1*val2)+(val2-val1))/val2
    shootNxt()
    shoot(result.2f)
 }
gameOver