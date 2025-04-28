# reverse fib
play() {
    hp i, n
    fib[1]: [0]
    n: loadNum("Enter a number: ")
    shootNxt()
    for i: 1, i <= n, i += 1 {
    	if i == 1 {
        	fib.join(1)
        } else {
        	num: fib[i-1] + fib[i-2]
        	fib.join(num)
        }
    }
    for i: rounds(fib)-1, i >= 0, i -= 1 {
    	shoot("{fib[i]} ")
    }
}



gameOver