# Activity - Number 19
play(){
  hp num
  num: loadNum("Enter number: ")

  if (num % 2 == 0) {
      shoot("\nThe number is even")
  } else {
      shoot("\nThe number is odd")
  }
}
gameOver