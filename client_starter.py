import socket
import pickle
from fl_networking_tools import get_binary, send_binary

'''
Commands:
JOIN - client requesting to join the quiz
QUES - question command
ANSW - sending answer
STAT - status of the quiz

Responses
0 - Invalid team name
1 - Join req confirmed
2 - Join req denied
3 - Question available
4 - Question 
5 - Correct answer
6 - Incorrect answer
8 - Quiz over
'''

def printQuestion(question):
    print(f"""
{question[0]}
a). {question[1][0]}  b). {question[1][1]}
c). {question[1][2]}  d). {question[1][3]}
""")

team_name = input("Enter your team name >>> ").upper()
server_address = input("Server Address >>> ")

playing = True

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((server_address, 2065))
except:
    print("Invalid address")
    exit()

send_binary(client_socket, ["JOIN", team_name])

print("""
Rules:

1). Team name is manditory
2). Team name should be minimum of 3 characters and maximum of 10 characters
3). Type down the correct option variable for the question asked
4). You will be awarded 3 lives at the start of the quiz
5). For each wrong answer you will be losing a life
6). You will be out of the game if you are out of lives
""")

while playing:
    for response in get_binary(client_socket):
        if response[0] == 0:
            print(response[1])
            team_name = input("Enter your team name >>> ").upper()
            send_binary(client_socket, ["JOIN", team_name])         

        elif response[0] == 1:
            print(f"Welcome team {team_name}")
            print("You have ⭐ ⭐ ⭐  lives")
            send_binary(client_socket,["STAT",""])

        elif response[0] == 2:
            print("OOPS! Connection failed")
            playing = False
            break

        elif response[0] == 3:
            print(response[1])
            send_binary(client_socket,["QUES",""])

        elif response[0] == 4:
            printQuestion(response[1])
            answer = input("Your answer >>> ")
            send_binary(client_socket,["ANSW",answer])

        elif response[0] == 5:
            print("CONGRATS! It's a right answer")
            print("Your score is " + str(response[1]))
            send_binary(client_socket,["STAT",""])

        elif response[0] == 6:
            no_of_lives = '⭐ '*response[1] if response[1] > 0 else "0 lives"
            print("OOPS! It's a wrong answer")
            print(f"You have {no_of_lives} left")
            send_binary(client_socket,["STAT",""])

        elif response[0] == 7:
            print("Your next question....")
            send_binary(client_socket,["QUES",""])
            
        elif response[0] == 8:
            print(response[1])
            playing = False
            break

client_socket.close()
exit()