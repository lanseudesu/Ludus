generate calc_average(num1, num2, num3) 
generate determine_grade(ave)

play() {
hp i
while true {
	num_students: loadNum("Enter the number of students: ")
    
    for i: 0, i < num_students, i+=1 {
    	name: load("\nEnter student name: ")
        score1: loadNum("\nEnter score for exam 1: ")
        score2: loadNum("\nEnter score for exam 2: ")
        score3: loadNum("\nEnter score for exam 3: ")
        
        average: calc_average(score1, score2, score3)
        grade: determine_grade(average)
        
        shootNxt("\n{name}'s final results: ")
        shootNxt("Average score: {average.2f}")
        shootNxt("Letter grade: {grade}")
    }
    
	response: load("Do you want to enter a new batch of students?[Y][N]: ")
    
	if response == "N" OR response == "n" {
		checkpoint
	}
    shootNxt()
}
}

generate calc_average(num1, num2, num3) {
	recall (num1 + num2 + num3) / 3
}

generate determine_grade(ave) {
	 if ave >= 90 {
        recall "A"
    } elif ave >= 80 {
        recall "B"
    } elif ave >= 70 {
        recall "C"
    } elif ave >= 60 {
        recall "D"
    } else {
        recall "F"
    }
}

gameOver
