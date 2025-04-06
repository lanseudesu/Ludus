generate choose_shape()
generate create_square(l)
generate create_rectangle(l,w)
generate create_triangle(h)
generate print_shape(result)

play() {
	shape: choose_shape()
    comms result
    shape: "S"
    flank shape {
    	choice "S":
        	length: loadNum("\nEnter length: ")
            result: create_square(5)
        	#result: create_square(length)
        choice "R":
        	length: loadNum("\n Enter length: ")
            shootNxt()
            width: loadNum("\n Enter width: ")
            result: create_rectangle(5, 7)
        	#result: create_rectangle(length, width)
        choice "T":
        	height: loadNum("\n Enter height: ")
            result: create_triangle(6)
        	#result: create_triangle(height)
        backup:
        	shoot("Invalid shape.")
    }
    
    if result != "" {
    	shootNxt()
    	print_shape(result)
    }
}

generate choose_shape(){
	input: load("Enter shape [S]quare [R]ectangle [T]riangle: ")
    recall input
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
        	result += "*"
        }
        result += "\n"
    }
    recall result
}

generate create_triangle(h){
	comms result
	if h < 1 {
    	shoot("Invalid inputs for rectangle.")
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

generate print_shape(result){
	shoot(result)
}

gameOver