#Activity - Number 12

generate mirroredRightTriangle(rows)

play() {
    num: loadNum("Enter number of rows: ")
    shootNxt("\n")
    mirroredRightTriangle(num)
}

generate mirroredRightTriangle(rows) {
    hp i, j

    if rows < 1 {
        shoot("Invalid input.")
    }

    for i: 1, i <= rows, i += 1 {
        for j: 1, j <= rows, j += 1 {
            if j <= rows - i {
                shoot(" ")
            } else {
                shoot("*")
            }
        }
        shoot("\n")
    }
}

gameOver
