# Activity - Number 6

play(){
    hp i
	for i: 1, i <= 5, i +=1  {  
    	hp j
        for j: 1, j <= i, j+=1 {  
            shoot("* ") 
        }
     	shootNxt()
    }
}

gameOver
