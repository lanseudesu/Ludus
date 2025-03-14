generate to_fahrenheit(c)

play() {
	xp celsius
    celsius: loadNum("Enter temperature in Celsius: ")

    fahrenheit: to_fahrenheit(celsius)
    shootNxt("{celsius.2f}°C is equal to {fahrenheit.2f}°F")
}

generate to_fahrenheit(c) {
    recall (c * 9.0 / 5.0) + 32.0
}

gameOver