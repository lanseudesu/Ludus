# Activity - Number 8
play() {
    shootNxt("Pyramid: \n")
    hp current_row, space, stars
 
    
     for current_row: 1, current_row <= 5, current_row += 1 {
         stars:0
         for space: 1, space <= 5 - current_row, space += 1 {
             shoot("  ")
         }

         while stars != 2 * current_row - 1 {
             shoot("* ")
             stars += 1
          }
         shoot("\n")
      }
    
}

gameOver