# Activity - Number 18 
generate square_perimeter(side)
generate rectangle_perimeter(length, width)
generate circle_perimeter(radius)
generate triangle_perimeter(base, a, c)

play(){
  xp perimeter, side, length, width, radius, base, side1, side2
  shootNxt("Choose a shape to compute for perimeter:")
  shootNxt("[1] Square [2] Rectangle [3] Circle [4] Triangle")
  operation: loadNum("Enter your choice: ")
  flank operation {
  	choice 1:
    	side: loadNum("\nEnter the side of the square: ")
        perimeter: square_perimeter(side)
        shoot("\nThe perimeter of the square is {perimeter.2f}.")
    choice 2:
    	length: loadNum("\nEnter the length of the square: ")
        width: loadNum("\nEnter the width of the square: ")
        perimeter: rectangle_perimeter(length, width)
        shoot("\nThe perimeter of the rectangle is {perimeter.2f}.")
    choice 3:
    	radius: loadNum("\nEnter the radius of the circle: ")
        perimeter: circle_perimeter(radius)
        shoot("\nThe perimeter of the circle is {perimeter.2f}.")
    choice 4:
    	base: loadNum("\nEnter the base of the triangle: ")
        side1: loadNum("\nEnter the left side of the triangle: ")
        side2: loadNum("\nEnter the right side of the triangle: ")
        perimeter: triangle_perimeter(base, side1, side2)
        shoot("\nThe perimeter of the triangle is {perimeter.2f}.")
    backup:
    	shoot("\nInvalid Choice!")
  }  
}

generate square_perimeter(side) {
	recall side * 4
}

generate rectangle_perimeter(length, width) {
	recall (length + width) * 2
}

generate circle_perimeter(radius) {
	recall 2 * 3.1415926 * radius
}

generate triangle_perimeter(base, a, c) {
	recall a + base + c
}

gameOver