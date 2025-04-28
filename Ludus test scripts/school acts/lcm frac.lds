#Activity - LCM fraction idk

play(){
    num1: loadNum("Insert numerator of the first fraction: ")
    den1:	loadNum("\nInsert denominator of the first fraction: ")
    num2: loadNum("\nInsert numerator of the second fraction: ")
    den2:	loadNum("\nInsert denominator of the second fraction: ")
    shootNxt()
    numA: den1
    numB: den2

    while numB != 0 {
		temp: numB
		numB: numA % numB
		numA: temp
    }
	lcd: toHp((den1 * den2) / numA)
    
    num2: num2 * (toHp(lcd/den2))
    den2: den2 * (toHp(lcd/den2))
    num1: num1 * (toHp(lcd/den1))
    den1: den1 * (toHp(lcd/den1))
    
    shootNxt("LCD: {lcd}")
    shootNxt("Equivalent fractions: {num1}/{den1} + {num2}/{den2}")
    sum: num1 + num2
    shoot("Sum: {sum}/{den2}")
 
}


gameOver