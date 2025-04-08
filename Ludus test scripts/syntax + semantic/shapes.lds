generate create_square(l)
generate create_rectangle(l,w)
generate create_left_triangle(h)
generate create_right_triangle(h)
generate create_triangle(h)

play() {
	shape: load("Enter shape [S]quare [R]ectangle [T]riangle: ")
    if shape == "T" || shape == "t" {
    	shape: load("Enter type of triangle [CT] Center triangle [LT] Left Triangle [RT] Right Triangle: ")
    }
    shape: levelUp(shape)
    comms result
    flank shape {
    	choice "LT":
        	height: loadNum("\nEnter height: ")
        	result: create_left_triangle(height)
        choice "RT":
        	height: loadNum("\nEnter height: ")
        	result: create_right_triangle(height) 
        choice "CT":
        	height: loadNum("\nEnter height: ")
        	result: create_triangle(height)    
    	choice "S":
        	length: loadNum("\nEnter length: ")
        	result: create_square(length)
        choice "R":
        	length: loadNum("\nEnter length: ")
            width: loadNum("\nEnter width: ")
        	result: create_rectangle(length, width)
        backup:
        	shoot("\nInvalid shape: {shape}")
    }
    
    if result != "" {
    	shootNxt()
    	shoot(result)
    }
}

generate create_square(l){
	comms result
	if l < 1 {
    	shoot("Invalid input for square.")
    }
	hp i
	for i: 0, i < l, i += 1{
    	hp j
    	for j: 0, j < l, j += 1{
        	result += "*  "
        }
        result += "\n"
    }
    recall result
}

generate create_rectangle(l, w){
	comms result
	if l < 1 OR w < 1 {
    	shoot("Invalid inputs for rectangle.")
    }
	hp i
	for i: 0, i < l, i += 1{
    	hp j
    	for j: 0, j < w, j += 1{
        	result += "* "
        }
        result += "\n"
    }
    recall result
}

generate create_left_triangle(h){
	comms result
	if h < 1 {
    	shoot("Invalid inputs for triangle.")
    }
	hp i
	for i: 0, i < h, i += 1{
    	hp j
    	for j: 0, j < (2 * i + 1), j += 1{
        	result += "*"
        }
        result += "\n"
    }
    recall result
}

generate create_right_triangle(h){
	comms result
	if h < 1 {
    	shoot("Invalid inputs for triangle.")
    }
	hp i
	for i: 0, i < h, i += 1{
    	x: ((h * 2) - (i * 2)) - 2
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

generate create_triangle(h){
	comms result
	if h < 1 {
    	shoot("Invalid inputs for triangle.")
    }
	hp i
	for i: 0, i < h, i += 1{
    	x: h - i - 1
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