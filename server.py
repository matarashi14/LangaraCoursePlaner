import socket
import threading

import pymongo
import json
import pprint

client = pymongo.MongoClient("")
dbs = client.list_database_names()
print(dbs)

Langara_db = client.LangaraCoursePlaner
collections = Langara_db.list_collection_names()
courses = Langara_db.courses
users = Langara_db.users

print(collections)

printer = pprint.PrettyPrinter()

AS_MANDATORY = ['CPSC 1050', 'CPSC 1160', 'CPSC 1181', 'CPSC 2150', 'CPSC 1150', 'CPSC 1280', 'MATH 2362', 'MATH 1171',
                'MATH 1271', 'CMNS 1118', 'ENGL 1123']

DP_MANDATORY = ['CPSC 1030', 'CPSC 1045', 'CPSC 1050', 'CPSC 1160', 'CPSC 1181', 'CPSC 1480', 'CPSC 2150', 'CPSC 1150',
                'CPSC 2221', 'CPSC 1280', 'CMNS 1118', 'ENGL 1123']

HEADER = 64
PORT = 5050
hostname = socket.gethostname()
# SERVER = socket.gethostbyname(hostname)
SERVER = '127.0.0.1'
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT'
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def main():
    start()


def insert_user(name, program, took_courses):
    doc = {"user_name": name, 'program': program, 'took_courses': took_courses}
    users.insert_one(doc)


def create_account(conn):
    is_exist = False
    while not is_exist:
        conn.send("Enter username: ".encode(FORMAT))
        user_name = conn.recv(2048).decode(FORMAT)

        if users.find_one({"user_name": user_name}):
            continue
        else:
            is_exist = True
    conn.send(
        "Enter your program: AS (Associate Degree in Computer Science) or DP (Diploma of Computer Studies) : ".encode(
            FORMAT))
    program = conn.recv(2048).decode(FORMAT)

    while program != 'AS' and program != 'DP':
        conn.send(
            "Enter your program: AS (Associate Degree in Computer Science) or DP (Diploma of Computer Studies) : ".encode(
                FORMAT))
        program = conn.recv(2048).decode(FORMAT)

    took_courses = []
    insert_user(user_name, program, took_courses)
    conn.send("create account successfully".encode(FORMAT))


def login(conn):
    is_exist = False
    while not is_exist:
        conn.send("Enter user name".encode(FORMAT))
        user_name = conn.recv(2048).decode(FORMAT)
        if users.find_one({"user_name": user_name}):
            is_exist = True

    conn.send("Log in successful...".encode(FORMAT))
    return user_name


def show_courses(conn):
    conn.send("Enter department you want to see: ".encode(FORMAT))
    department = conn.recv(2048).decode(FORMAT)
    c = courses.find({'Department': department})
    courses_list = list(c)
    str = ""
    for x in courses_list:
        str = str + x.get('Course_id') + " " + x.get('Course_name') + "\n"
    conn.send(str.encode(FORMAT))


def was_take(user_name, course_name) -> bool:
    user = users.find_one({"user_name": user_name})
    courses_list = user['took_courses']
    for c in courses_list:
        if c == course_name:
            return True

    return False


def registered_took_courses(user_name, conn):
    is_exist = False
    while not is_exist:
        conn.send("Enter course id  (eg: CPSC 1280):  ".encode(FORMAT))
        course_input = conn.recv(2048).decode(FORMAT)

        if courses.find_one({"Course_id": course_input}):
            if was_take(user_name, course_input):
                conn.send("You already took this class\n".encode(FORMAT))
                is_exist = False
            else:
                is_exist = True
    users.update_one({"user_name": user_name}, {
                     "$push": {'took_courses': course_input}})
    conn.send("added the course successfully".encode(FORMAT))


def display_took_courses(user_name, conn):
    user = users.find_one({"user_name": user_name})
    if user['took_courses']:
        courses_list = user['took_courses']
        str = ""
        for x in courses_list:
            # str = str + x.get('Course_id') + " " + x.get('Course_name') + "\n"
            str = ', '.join(courses_list)
        conn.send(str.encode(FORMAT))
    else:
        conn.send("None".encode(FORMAT))


def mandatory_courses(user_name, conn):
    user = users.find_one({"user_name": user_name})
    p = user['program']
    if p == 'AS':
        str = ', '.join(AS_MANDATORY)
    elif p == 'DP':
        str = ', '.join(DP_MANDATORY)
    conn.send(str.encode(FORMAT))


def elective_courses(conn):
    conn.send("Enter department you want to see: ".encode(FORMAT))
    department = conn.recv(2048).decode(FORMAT)
    conn.send("Enter attribute (eg. UT, LSI, 2AR etc...) : ".encode(FORMAT))
    attribute = conn.recv(2048).decode(FORMAT)
    c = courses.find({'Department': department, attribute: 'Y'})
    courses_list = list(c)
    str = ""
    for x in courses_list:
        str = str + x.get('Course_id') + " " + x.get('Course_name') + "\n"
    conn.send(str.encode(FORMAT))


def graduation_evaluation(user_name, conn):
    if check_graduation(user_name):
        conn.send("Congratulation!!! You are eligible to graduate!".encode(FORMAT))
    else:
        conn.send("You need to take more courses.".encode(FORMAT))


def check_graduation(user_name) -> bool:
    user = users.find_one({'user_name': user_name})
    took_course = user['took_courses']
    print(took_course)
    program = user['program']

    if program == 'AS':
        c_list = AS_MANDATORY
    elif program == 'DP':
        c_list = DP_MANDATORY

    for c in c_list:
        if c in took_course:
            took_course.remove(c)

    # for AS
    two_UT_arts_AS = 0
    two_2SC = 0
    one_second_year_CPSC = 0
    three_UT = 0
    one_lab = 0

    # for DP
    one_BUSM = 0
    three_second_CPSC = 0
    four_UT = 0

    if took_course == []:
        return False
    else:
        for cou in took_course:
            c = courses.find_one({'Course_id': cou})
            if program == 'AS':
                if c.get('LSC') == 'Y':
                    one_lab += 1
                elif c.get('2SC') == 'Y' and c.get('Department') == 'Computer Science' and one_second_year_CPSC != 1:
                    one_second_year_CPSC += 1
                elif c.get('2SC') == 'Y' and two_2SC != 2:
                    two_2SC += 1
                elif c.get('HUM') == 'Y' or c.get('SOC') == 'Y' and two_UT_arts_AS < 2:
                    two_UT_arts_AS += 1
                elif c.get('UT') == "Y":
                    three_UT += 1
            elif program == 'DP':
                if c.get('Department') == 'Business Management':
                    one_BUSM += 1
                elif c.get('2SC') == 'Y' and c.get('Department') == 'Computer Science':
                    three_second_CPSC += 1
                elif c.get('UT') == "Y":
                    four_UT += 1

    if program == 'AS' and one_second_year_CPSC >= 1 and one_lab >= 1 and two_2SC >= 2 and two_UT_arts_AS >= 2 and three_UT >= 3:
        return True
    elif program == 'DP' and one_BUSM >= 1 and three_second_CPSC >= 3 and four_UT >= 4:
        return True
    else:
        return False


def print_help(conn):
    conn.send(
        "[c] = create account : [l] = login : [s] = show courses : [d] = display taken course\n"
        "[r] = register course : [m] = show mandatory courses : [e] = elective course \n"
        "[g] = graduation evaluation : [o] = logout : [t] = terminate program"
        .encode(FORMAT))


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    user_name = ""
    while connected:
        action = conn.recv(2048).decode(FORMAT)

        print(f"[{addr}]: {action}")

        if action == 'c':
            create_account(conn)
        elif action == 'l':
            user_name = login(conn)
        elif action == 's':
            show_courses(conn)
        elif action == 'r':
            registered_took_courses(user_name, conn)
        elif action == 'd':
            display_took_courses(user_name, conn)
        elif action == 'm':
            mandatory_courses(user_name, conn)
        elif action == 'e':
            elective_courses(conn)
        elif action == 'g':
            graduation_evaluation(user_name, conn)
        elif action == '--help':
            print_help(conn)
        elif action == 'o':
            user_name = ""
            conn.send("Log out successfully".encode(FORMAT))
        elif action == 't':
            connected = False
        else:
            conn.send("Invalid message".encode(FORMAT))

    conn.close()


def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE THREAD]: {threading.activeCount() - 1}")


if __name__ == '__main__':
    main()
