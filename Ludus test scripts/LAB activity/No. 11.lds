# Activity - Number 11
generate rightTriangle(size)

play(){
	height: loadNum("Enter triangle height: ")
    shootNxt("\n")
    rightTriangle(height)
}

generate rightTriangle(size){
	hp i
	for i: 1, i <= size, i +=1  {  
    	hp j
        for j: 1, j <= i, j+=1 {  
            shoot("* ") 
        }
     	shootNxt()
    }
}
gameOver
