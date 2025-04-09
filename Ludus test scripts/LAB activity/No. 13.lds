# Activity - Number 13
generate pyramid(total_rows)

play() {
    num: loadNum("Enter number of rows: ")
    shootNxt("\n")
    pyramid(num)
}

generate pyramid(total_rows) {
	hp current_row, space, stars
    
    if total_rows <= 1 {
    	shoot("Invalid input for pyramid.")
    } else {
    
      for current_row: 1, current_row <= total_rows, current_row += 1 {
          stars:0
          for space: 1, space <= total_rows - current_row, space += 1 {
              shoot("  ")
          }

          while stars != 2 * current_row - 1 {
              shoot("* ")
              stars += 1
          }
        shoot("\n")
      }
   }
}

gameOver