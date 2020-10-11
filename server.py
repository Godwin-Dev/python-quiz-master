import socketserver,socket
from collections import namedtuple
from threading import Event
from fl_networking_tools import get_binary, send_binary
from random import choice

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

# Getting the device IP address
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
server_address = ip_address
print(f'Server Address: {server_address}')

while True:
    try:
        number_of_teams = int(input("Maximum number of teams >>> "))
        break
    except :
        print("Give a valid number")

teams = []
current_question = None
ready_to_start = Event()
wait_for_answers = Event()

answered = 0
scores = {}
lives = {}
 
Question = namedtuple('Question', ['q','options', 'answer'])

quiz_questions = [
    Question("Expand the acronym ALU",["Application Logic Unit","Algorithmic Logic Unit","Arithmetic Logic Unit","Additional Logorithmic Unit"], "c"),
    Question("What does RAM stand for?",["Read Access Memory","Random Access Memory","Random Application Memory","Rapid Application Machine"], "b"),
    Question("The brain of any computer system is",["ALU","RAM","CPU","ROM"], "c"),
    Question("Which of the following languages is more suited to a structured program?",["PL/1","FORTRAN","BASIC","PASCAL"], "d"),
    Question("Which of the following is the 1's complement of 10?",["01","101","11","00"], "a"),
    Question("A computer program that converts assembly language to machine language is",["Compiler","Interpreter","Comparator","Assembler"], "d"),
    Question("The time required for the fetching and execution of one simple machine instruction is",["Delay time","CPU cycle","Real time","Execution time"], "b"),
    Question("The symbols used in an assembly language are",["Mnemonics","Codes","Assembler","Integers"], "a"),
    Question("A single packet on a data link is known as",["Path","Frame","Block","Group"], "b"),
    Question("The 2's complement of a binary no. is obtained by adding.....to its 1's complement.",["0","10","1","01"], "c"),
]

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class QuizGame(socketserver.BaseRequestHandler):
    # The handle method is what actually handles the connection
    def handle(self):
        #Retrieve Command
        global teams, answered, current_question, scores
        for command in get_binary(self.request):
            if command[0] == "JOIN":
                team_name = command[1]
                if team_name == "":
                    send_binary(self.request,[0,"Team name is manditory. Please enter a valid name"])
                elif len(team_name)<3 or len(team_name)>10:
                    send_binary(self.request,[0,"Team name should be minimum of 3 characters and maximum of 10 characters"])
                elif team_name in teams:
                    send_binary(self.request,[0,"Team name already taken. Try a new one"])
                else:
                    teams.append(team_name)
                    scores[team_name] = 0
                    lives[team_name] = 3
                    if len(teams) == number_of_teams:
                        send_binary(self.request,[1,""])
                        ready_to_start.set()
                    elif len(teams) < number_of_teams:
                        send_binary(self.request,[1,""])
                    elif len(teams) > number_of_teams:
                        send_binary(self.request,[2,""])        
                        teams.pop()

                    ready_to_start.wait()

            elif command[0] == "STAT":
                if len(quiz_questions) == 0:
                    max_score = max(scores,key=scores.get)
                    min_score = min(scores,key=scores.get)
                    if min_score == max_score:
                        send_binary(self.request, (8, "It's a tie"))
                    else:
                        winners = []
                        for score in scores:
                            if max_score == score:
                                winners.append(score)
                        if len(winners) == 1:
                            send_binary(self.request, (8, f"Team {winners[0].upper()} won the quiz"))
                        else:
                            send_binary(self.request, (8, f"Teams {','.join(winners).upper()} won the quiz"))
                    continue
                if ready_to_start.isSet() and not wait_for_answers.isSet():
                    send_binary(self.request, [3, "Quiz is starting!"])
                elif ready_to_start.isSet() and wait_for_answers.isSet():
                    if len(teams) == 1:
                        send_binary(self.request, (8, "Congrats you have won the quiz, all of your opponents have been eliminated"))
                    else:
                        send_binary(self.request, [3, "Your next question......"])

            elif command[0] == "QUES":
                if len(teams) == 1:
                    send_binary(self.request, (8, "Congrats you have won the quiz, all of your opponents have been eliminated"))
                else:
                    if current_question == None:
                        current_question = choice(quiz_questions)
                        wait_for_answers.clear()

                    send_binary(self.request, (4, [current_question.q,current_question.options]))
            
            elif command[0] == "ANSW":
                if command[1].lower() == current_question.answer.lower():
                    scores[team_name] += 1
                    if len(teams) == 1:
                        send_binary(self.request, (8, "Congrats you have won the quiz, all of your opponents have been eliminated"))
                    else:
                        response = 5
                        send_binary(self.request,[response,scores[team_name]])
                else:
                    lives[team_name] -= 1
                    if lives[team_name] == 0:
                        teams.remove(team_name)
                        answered -= 1
                        response = 8
                        send_binary(self.request, (response, "You lost. Out of lives"))
                    else:
                        response = 6
                        send_binary(self.request,[response,lives[team_name]])
                answered += 1
                if answered == len(teams):
                    quiz_questions.remove(current_question)
                    current_question = None
                    answered = 0
                    wait_for_answers.set()
                
                wait_for_answers.wait()

quiz_server = ThreadedTCPServer((server_address, 2065), QuizGame)
quiz_server.serve_forever() 