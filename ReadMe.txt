5x5 Matrix Game - Sprint 1

Game Files
-----
sprint1.py - The main game file with everything in it
  - AuthManager class: handles player registration and login
  - LoginScreen class: the login/register screen shown at startup
  - TimeLimitScreen class: the time limit setup screen shown before each level
  - GameBoard class: handles the game logic and rules
  - Button class: for the UI buttons
  - SoundManager class: makes the beep sounds
  - GameGUI class: draws everything and handles clicks


User Stories
---------------------------
1. GUI window - you click on cells instead of typing coordinates
2. Sound effects - beeps when you place numbers or make mistakes
3. Shows the next number - so you don't have to remember
4. Clear button - restart if you mess up
5. Undo button - go back as many moves as you want
6. Error sounds - different beep for invalid moves
7. Game logging - saves your completed games to a JSON file
8. Level 2 - outer ring

9. Level 3 expansion - after a player successfully completes Level 2, the game unlocks Level 3. In Level 3 the outer ring remains filled from Level 2, while the inner board numbers (except the number 1) are hidden. The player must rebuild numbers 2–25 again using the constraints provided by the outer ring positions.

10. Reward system - players receive one point for every number successfully placed on the board in any level. If a move is undone or rolled back, one point is removed. Points accumulate across all levels so players can see their overall performance.

11. Time limit - set a time limit per level with bonus/penalty scoring
14. Authentication - players must register and log in before playing
15. Hint system - optional button that briefly highlights all valid adjacent moves for the next number in Level 1
16. Leaderboard - saves top 10 scores (name, score, level, timestamp) and shows them in a Top 10 overlay


What You Need
-------------
- Python 3.8 or higher
- pygame library
- numpy library for sounds


How to Install
--------------
1. Make sure you have Python installed

2. Install the libraries:
   pip install pygame numpy

   (or pip3 if that's what works on your system)


How to Run
----------
run:
   python3 sprint1.py


How to Play
-----------
Login / Register:
- When you launch the game a login screen appears
- New players: type a username and password, then click Register
- Returning players: type your credentials and click Login (or press Enter)
- You cannot access the game without logging in first
- Credentials are saved in users.json (passwords are hashed)


Time Limit (Level 1):
- After logging in, a time limit screen appears for Level 1
- Enter any number of seconds (e.g. 30, 60, 80) and click Start Game
- Click No Limit to play without a timer
- The countdown is shown on the left side of the screen during play
- Finishing early earns +1 point per unused second
- Going over costs -1 point per extra second (score floored at 0)


Level 1:
- The game starts with 1 already placed randomly
- Click on cells next to the last number to place 2, 3, 4, etc.
- Numbers must be adjacent (including diagonally)
- Get +1 point for diagonal placements
- Fill all 25 cells to beat Level 1


Level 2:
- Click the "Level 2" button after beating Level 1
- A time limit screen appears so you can set a separate limit for Level 2
- Now place numbers 2-25 on the outer ring
- Where you can place depends on where that number is on the inner board
- Basically row/column ends, plus corners if it's on a diagonal
- Fill all 24 outer cells to beat Level 2


Level 3:
- Level 3 unlocks automatically after completing Level 2
- The outer ring from Level 2 remains visible
- Inner board numbers (except 1) are hidden
- Players must rebuild numbers 2–25 on the inner board using the constraints from the outer ring


Buttons:
- New Game: starts over
- Clear: clears the current level
- Undo: removes your last move
- Level 2: activates Level 2 after you beat Level 1
- Hint: one-time highlight of valid cells for the next move in Level 1
- Top 10: toggles a leaderboard overlay showing the top 10 scores


Scoring
-------
+1 point for each number successfully placed
-1 point for each undo or rollback
Points accumulate across levels
Time bonus: +1 point per second remaining when you finish within the limit
Time penalty: -1 point per second over the limit (score cannot go below 0)


Output
------
When you finish a level, it saves to game_log.json with:
- Your name (from login)
- Date and time
- Which level
- Your score
- The full board


If Something Breaks
-------------------
- No sound? You probably don't have numpy installed
- pygame won't install? Try: pip install --upgrade pip first
- On Linux you might need: sudo apt-get install python3-pygame


What we Used
-----------
- Python 3.9
- Pygame for the GUI
- numpy for sound generation
- JSON for saving games
- VS Code for editing


Files in this folder:
--------------------
Proj1/
  sprint1.py         - the actual game
  ReadMe.txt         - this file
  users.json         - registered player accounts (appears after first registration)
  game_log.json      - saved games (appears after you beat a level)
  QUICK_START.txt    - shorter instructions
  USER_STORIES_IMPLEMENTATION.txt - detailed implementation notes