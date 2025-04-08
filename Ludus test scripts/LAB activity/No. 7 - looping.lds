# Activity - Number 7

play() {
    hp i, j
    num: 7
    for i: 1, i <= num, i += 1 {
        for j: 1, j <= num, j += 1 {
            if j <= num - i {
                shoot(" ")
            } else {
                shoot("*")
            }
        }
        shoot("\n")
    }
}

gameOver
