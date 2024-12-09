# Global declarations must always be placed at the topmost part of the module.
immo greeting: "Welcome to Ludus!"  
comms userName  
hp userAge  

# Global declarations include constants, variables, and arrays.
# These can be declared in any order.

generate displayUserInfo()  # Function declaration
build UserInfo              # Global struct declaration

play() {  # Main function begins here

    access UserInfo user: "John", 21  
    displayUserInfo(user)  

}

generate displayUserInfo(user) {  # Function body
    shootNxt("Hello, {user.name}!")  
    shootNxt("You are {user.age} years old.")  
}

build UserInfo {  # Global struct body
    comms name,  
    hp age  
}

gameOver  # Terminator keyword
