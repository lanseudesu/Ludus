#Activity - 15

generate rectangle(rows, cols)

play() {
	 rows: loadNum("Enter number of rows: ")
     cols: loadNum("\nEnter number of columns: ")
     shootNxt()
     
     rectangle(rows, cols)
     
}

generate rectangle(rows, cols){
	hp i, j
    
     if rows <= 1 {
        shoot("Invalid number of rows.")
    } elif cols <= 1 {
        shoot("Invalid number of columns.")
    }
    
	for i: 0, i < rows, i+=1 {
            for j: 0, j < cols, j+=1 {
                shoot("*")
            }
            shootNxt()
  }
 }
gameOver
