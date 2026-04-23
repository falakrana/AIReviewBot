def calculate_sum(a, b):
    # TODO: Add validation
    return a + b

class DatabaseHandler:
    def connect(self):
        try:
            print("Connecting to DB...")
        except:
            print("Error connecting")

def insecure_function(user_input):
    exec(user_input)
