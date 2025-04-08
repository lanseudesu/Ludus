#Activity - Number 10 (for loop)
play() {
	 hp i, j
	 rows: 6
     cols: 8
     
     for i: 0, i < rows, i+=1 {
            for j: 0, j < cols, j+=1 {
                shoot("*")
            }
            shootNxt()
  }
}
gameOver
