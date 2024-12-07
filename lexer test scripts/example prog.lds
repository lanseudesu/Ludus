flank day { 
     choice "Monday": 
           shootNxt("It's the start of the work week.") 
           resume 
     choice "Wednesday": 
          shootNxt("We're halfway through the week!")
          resume 
      backup: 
      shootNxt("Enjoy your day!") 
}
