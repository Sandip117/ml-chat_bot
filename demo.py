from pymongo import MongoClient
import pprint

MONGO_DETAILS = 'mongodb://localhost:27017'
client = MongoClient(MONGO_DETAILS)
database = client.database
student_collection = database.get_collection("student_collection")


def add_data():
    students = [
        {"name": "Jack", "age": 27, "gender": "female", "course": "Programing Design Paradigm"},
        {"name": "Tom", "age": 24, "gender": "male", "course": "Managing Software Development"},
        {"name": "Jill", "age": 27, "gender": "female", "course": "Programing Design Paradigm"},
        {"name": "Tony", "age": 22, "gender": "male", "course": "Algorithms"},
        {"name": "Jenny", "age": 23, "gender": "female", "course": "Robotics"},

    ]
    students_list = student_collection.insert_many(students)


def get_data():
    results = [student for student in student_collection.find()]
    return results


def show_data(records):
    for record in records:
        pprint.pprint(record)


def remove_data():
    for student in student_collection.find():
        student_collection.delete_one({"_id": student["_id"]})


def find_students_by_name(search_name: str):
    results = student_collection.find({"name": search_name})
    return results


def search_students(search_name: str):
    results = student_collection.find({"$text": {"$search": search_name}})
    return results


def search_students_and_score(search_key: str):
    results = student_collection.find(
        {"$text": {"$search": search_key}},
        {"score": {"$meta": "textScore"}}
    )
    return results


def create_index():
    student_collection.create_index([("name", "text"),
                                     ("course", "text")],
                                       name="name_index")


def show_indexes():
    indexes = student_collection.list_indexes()

    for index in indexes:
        pprint.pprint(index)


def delete_index():
    student_collection.drop_index("name_text")

#def search_students_and_sort
remove_data()
add_data()
#show_data(get_data())


#show_data(find_students_by_name("Jill"))
#create_index()
#show_indexes()
#delete_index()

#show_data(search_students("jill, robotics"))

show_data(search_students_and_score("jill jenny robotics"))

