# MT Assist
Mastery Test Assistant is a dedicated test management software, developed for remote sessions during the COVID19 pandemic.

MT Assist is designed specifically for Otago University's COMP150 (Python) paper, which has since been replaced with a new curriculum.

## Situation
* An excessively long Excel spreadsheet of questions:
  * Takes significantly long to navigate through for each student;
  * Question variation selection is prone to human bias, thus reducing a student's mark integrity;
  * Poses a risk of developing RSI for lab demonstrators.
* No student oversight:
  * Students can save, share, or practise on test questions outside of testing;
  * It is difficult for lab demonstrators to track student test durations (in particular accross empolyee shifts).
* Lack of cohesion between lab demonstrators who are all working remotely:
  * Answers marked by a different lab demonstrator than the test distributor made finding the relevent question difficult and time consuming;
  * Lab demonstrators who have just started their shift are unaware of who the current examinees are until they request marking;
  * Should human error occur in the marking process, there is an insufficient data trail to determine the validity of the student's claims.
  
## Solution
* Time Reduction:
  * Split the spreadsheet into individual TXT files within a directory heirachy of Progression No.>Categories>Variations;
  * Single button click is required to select a progression number for the master test;
  * Randomly selected variations of each category are read in and composed into the view window together with the test rules;
  * A second click
