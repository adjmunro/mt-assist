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
* Test Deployment:
  * Split the spreadsheet into individual TXT files within a directory heirachy of Progression No.>Categories>Variations;
  * Single button click is required to select a progression number for the master test;
  * Randomly selected variations of each category are read in and composed into the view window together with the test rules;
  * A second click copies all questions and rules to clipboard, so that it can be pasted into a messaging client (MS Teams, in our case).
* Test ID:
  * All compositions come with a unique identifying code, which represents the progression number, categories, variation number, and test start datetime;
  * When marking, the unique identifying code can be pasted into the search box, to retrieve the exact questions, and the student's test duration;
  * Loading a local copy of the questions massively helps with lab demonstrators cohesion and marking speed;
  * Recording the student's test duration verifies the integrity of their effort by ensuring none submit over the time limit;
  * Tracking the test duration of each student in the marking window also helps lab demonstrators inform students of their time remaining, time management planning, and recording students who left the test incomplete without notifying the demonstrator (for administration purposes).
* Some basic colour formatting was also added to help with the readability of the questions for demonstrators.
* The marking window, keeps a data trail of students' tests, which allows lab demonstrators to easily exchange results and ensure everyone has been marked off. 
