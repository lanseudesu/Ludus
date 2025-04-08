# Activity - Number 17 
generate square_area(side)
generate rectangle_area(length, width)
generate circle_area(radius)
generate triangle_area(base, height)

play(){
  xp area, side, length, width, radius, base, height
  shootNxt("Choose a shape to compute for area:")
  shootNxt("[1] Square [2] Rectangle [3] Circle [4] Triangle")
  operation: loadNum("Enter your choice: ")
  flank operation {
  	choice 1:
    	side: loadNum("\nEnter the side of the square: ")
        area: square_area(side)
        shoot("\nThe area of the square is {area.2f}.")
    choice 2:
    	length: loadNum("\nEnter the length of the square: ")
        width: loadNum("\nEnter the width of the square: ")
        area: rectangle_area(length, width)
        shoot("\nThe area of the rectangle is {area.2f}.")
    choice 3:
    	radius: loadNum("\nEnter the radius of the circle: ")
        area: circle_area(radius)
        shoot("\nThe area of the circle is {area.2f}.")
    choice 4:
    	base: loadNum("\nEnter the base of the triangle: ")
        height: loadNum("\nEnter the height of the triangle: ")
        area: triangle_area(base, height)
        shoot("\nThe area of the triangle is {area.2f}.")
    backup:
    	shoot("\nInvalid Choice!")
  }  
}

generate square_area(side) {
	recall side * side
}

generate rectangle_area(length, width) {
	recall length * width
}

generate circle_area(radius) {
	recall 3.1415926 * radius^2
}

generate triangle_area(base, height) {
	recall base * height / 2
}

gameOver