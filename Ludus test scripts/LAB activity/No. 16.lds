# Activity - Number 16
generate square(size)
generate rectangle(length, width)
generate triangle(height)
generate right_triangle(height)
generate inverted_right_triangle(height)

play() {
    shootNxt("Enter shape you want to display:")
    shootNxt("Press [1] - Square")
    shootNxt("Press [2] - Rectangle")
    shootNxt("Press [3] - Triangle")
    shootNxt("Press [4] - Right Triangle")
    shootNxt("Press [5] - Inverted Right Triangle")
	shape: loadNum()
    comms result
    flank shape {
    	choice 1:
        	size: loadNum("\nEnter size: ")
        	result: square(size)
        choice 2:
        	length: loadNum("\nEnter length: ")
            width: loadNum("\nEnter width: ")
        	result: rectangle(length, width)
        choice 3:
        	height: loadNum("\nEnter height: ")
        	result: triangle(height)    
    	choice 4:
        	height: loadNum("\nEnter height: ")
        	result: right_triangle(height) 
        choice 5:
        	height: loadNum("\nEnter height: ")
        	result: inverted_right_triangle(height) 
        backup:
        	shoot("\nInvalid shape: {shape}")
    }
    
    if result != "" {
    	shootNxt("\n")
    	shoot(result)
    }
}

generate square(size){
	comms result
	if size <= 1 {
    	recall "Invalid input for square."
    }
	hp i
	for i: 0, i < size, i += 1{
    	hp j
    	for j: 0, j < size, j += 1{
        	result += "*  "
        }
        result += "\n"
    }
    recall result
}

generate rectangle(length, width){
	comms result
	if length <= 1 OR width <= 1 {
    	recall "Invalid inputs for rectangle."
    }
	hp i
	for i: 0, i < length, i += 1{
    	hp j
    	for j: 0, j < width, j += 1{
        	result += "* "
        }
        result += "\n"
    }
    recall result
}

generate triangle(height){
	comms result
	if height <= 1 {
    	recall "Invalid input for triangle."
    }
	hp i
	for i: 0, i < height, i += 1{
    	x: height - i - 1
    	hp j
        for j: 0, j < x, j += 1{
        	result += " "
        }
    	for j: 0, j < (2 * i + 1), j += 1{
        	result += "*"
        }
        result += "\n"
    }
    recall result
}

generate right_triangle(height){
	comms result
	if height <= 1 {
    	recall "Invalid input for triangle."
    }
	hp i
	for i: 0, i < height, i += 1{
    	hp j
    	for j: 0, j < (2 * i + 1), j += 1{
        	result += "*"
        }
        result += "\n"
    }
    recall result
}

generate inverted_right_triangle(height){
	comms result
	if height <= 1 {
    	recall "Invalid input for triangle."
    }
	hp i
	for i: 0, i < height, i += 1{
    	x: ((height * 2) - (i * 2)) - 2
    	hp j
        for j: 0, j < x, j += 1{
        	result += " "
        }
    	for j: 0, j < (2 * i + 1), j += 1{
        	result += "*"
        }
        result += "\n"
    }
    recall result
}

gameOver