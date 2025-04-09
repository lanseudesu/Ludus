#No. 14 - function call (square)

generate square(rows)

play(){
	rows: loadNum("Enter number of rows: ")
    shootNxt("\n")
	square(rows)
}

generate square(rows){
    if rows <= 1 {
    	shoot("Invalid input.")
    } else {
      hp i, j
      for i: 0, i < rows, i+=1{
       for j: 0, j < rows, j+=1{
          shoot("* ")
          }
       shootNxt()
      }
    }
}
gameOver