# Activity - Number 11
generate rightTriangle(size)

play(){
	height: loadNum("Enter triangle height: ")
    shootNxt("\n")
    rightTriangle(height)
}

generate rightTriangle(size){
	if size <= 1 {
    	shoot("Invalid triangle height, must be more than 1.")
    } else {
      hp i
      for i: 1, i <= size, i +=1  {  
          hp j
          for j: 1, j <= i, j+=1 {  
              shoot("* ") 
          }
          shootNxt()
       }
    }
}
gameOver
