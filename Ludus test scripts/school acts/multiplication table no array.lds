play() {
	hp input, i, j
    input: loadNum("Insert an integer: ")
    shootNxt()
 	for i: 1, i <= input, i += 1{
    	for j: 1, j <= input, j += 1 {
        	dig: j * i
            if dig < 10 {
        		shoot("{dig}   ")
            } elif dig >= 10 && dig < 100 {
        		shoot("{dig}  ")
            } else {
            	shoot("{dig} ")
            }
            
    	}
    	shootNxt()
    }
}
gameOver