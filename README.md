#   AMQ Auto Complete

This is a simple script that log you into your account and is able to auto solve the Quiz.

##  Installation

1. Install Python 3.5 or higher
2. Install the dependencies by running `pip install -r requirements.txt`
3. Set your username and password in a `.env` file at the root of the project as `USER` and `MDP`.
4. Run the script by running `python main.py`

##  Usage

Join a game and the bot will automatically try to solve the quiz. If it is unable to solve the quiz, you will have to solve it yourself. The script will then add the correct answer provided by the website to his database.

##  Notes

* The script will only solve the quiz if it is able to solve it with 100% accuracy. It will provide a link to the opening video in the terminal so you can try to guess it yourself.


##  Changelog

### v1.0.0
* Initial release
