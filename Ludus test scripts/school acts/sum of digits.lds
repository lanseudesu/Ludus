#Activity - sum of digits
generate digit_sum(num)

play(){
	hp input
  	input: loadNum("Enter an integer: ")
   	shootNxt()
   	digit_sum(toComms(input))
}

generate digit_sum(num){
    hp i, sum
    flag neg
    if num[0] == "-" {
    	neg: true
        num.drop(0)
    }
    for i:0, i< rounds(num), i+=1{
    	dig: num[i]
    	sum += toHp(dig)
    }
    if neg {
    	shoot("The sum of every digit in -{num} is -{sum}")
        recall void
    }
	shoot("The sum of every digit in {num} is {sum}")
}

gameOver