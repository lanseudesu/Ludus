generate checkTemp(list)
play() {

	temp[5]: [34.5, 36.0, 37.1, 38.55, 39.02]
    checkTemp(temp)

}
generate checkTemp(list){
	hp i
    for i: 0, i < rounds(list), i += 1{
    	if list[i] < 38 && list[i] > 35 {
        	shootNxt("{(list[i]).2f} is = Normal temp")
        } elif list[i] < 35 {
        	shootNxt("{(list[i]).2f} is = Hypothermia")
        } elif list[i] > 38 {
        	shootNxt("{(list[i]).2f} is = Fever")
        }
    }
}
gameOver