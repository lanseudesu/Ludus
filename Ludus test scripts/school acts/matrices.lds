#Activity - LCM fraction idk
hp i,j,k
generate multiply_matrices(arr1, arr2)

play(){
 	hp matrix[][]
    A[2][3]: [1, 2, 3],[4, 5, 6]
	B[3][2]: [7, 8],[9, 10],[11, 12]
    matrix: multiply_matrices(A, B)
    for i: 0, i < 2, i += 1 {
    	shoot("[ ")
        for j: 0, j < 2, j += 1 {
        	shoot("{matrix[i][j]} ")
            
        }
        shootNxt("]")
    }
}

generate multiply_matrices(arr1, arr2){
    
    hp matrix[][]
    for i: 0, i < 2, i += 1 {
        for j: 0, j < 2, j += 1 {
            matrix[i].join(0)
        }
    }
    
    for i: 0, i < 2, i += 1 {
        for j: 0, j < 2, j += 1 {
            for k: 0, k < 3, k += 1 {
                matrix[i][j] += arr1[i][k] * arr2[k][j]
            }
        }
    }
    
    recall matrix
}
gameOver