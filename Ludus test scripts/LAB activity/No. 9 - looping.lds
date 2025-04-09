# No. 9 - looping (square)

play(){
	rows: 5
    
    hp i, j
	for i: 0, i < rows, i+=1{
	 for j: 0, j < rows, j+=1{
	 	shoot("* ")
			}
	 shootNxt()
		}
	}

gameOver