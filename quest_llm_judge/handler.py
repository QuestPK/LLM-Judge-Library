from flask import Flask, request, jsonify

class LlmJudge:
    """
    A LlmJudge object represents a Flask endpoint to retrieve the answer to a question using the
    specified bot function. The endpoint is created programmatically using the create_testing_rag_endpoint method.

    Attributes:
    - route: The URL route (string) to the endpoint.
    """

    def __init__(self, history_accepted:bool = False, route:str = '/get_rag_response'):
        """
        Initializes a LlmJudge object.

        Parameters:
        - route: The URL route (string) to the endpoint.
        """
        self.route = route
        self.history_accepted = history_accepted

    def __str__(self):
        return f"LlmJudge(route={self.route})"
    
    def create_rag_response_endpoint(self, app, get_query_response, methods=["POST"]):
        """
        Adds a new endpoint to the Flask app programmatically.

        Parameters:
        - app: Flask app object.
        - get_query_response: The function to get the query response.
        - methods: List of HTTP methods (default is ["POST"]).

        Endpoint can recieve below json payloads

        Expects a JSON payload containing either a 'questions' list, a 'question' string or a 'presets' dictionary.

        1) If a 'questions' list is provided, each question entry should have the following structure:
        {
            "id": <string>,  # Unique identifier for the question
            "question": <string>  # The question to be answered
        }
        Output:
        Returns a dictionary with 'answer' key containing a list of answers corresponding to the questions if a 'questions' list is provided.
        {
            "answer": [
                {
                    "id": <string>,  # Unique identifier for the question
                    "answer": <string>  # The answer to the question
                },
                ...
        ]}

        2) If a 'question' string is provided, it will be answered directly.
        {
            "question": <string>  # The question to be answered
        }
        Output:
        Returns a dictionary with a 'answer' key containing a single answer if a 'question' string is provided.
        {
            "answer": <string>  # The answer to the question
        }

        3) If a 'presets' dictionary is provided, it should contain a 'history_accepted' boolean to toggle the history acceptance.
        {
            "presets": {
                "history_accepted": <boolean>
            }
        }
        Returns a dictionary with 'response' and 'message' keys containing success message.
        Output:
        {
            "response": "Sucess",
            "message" : "History accepted: <boolean>"   
        }

        Returns:
        {"error": <string>}
        """
        endpoint_function = self.get_rag_response_function(get_query_response)
        app.add_url_rule(self.route, view_func=endpoint_function, methods=methods)

    def handle_qestions_list(self, questions_list: list, get_query_response):
        """
        Handles a list of questions and returns a list of answers.

        Parameters:
        - questions_list: A list of question dictionaries.

        Returns:
        - A list of answer dictionaries.
        """
        answers_list = []
        for question in questions_list:
            try:
                answer = get_query_response(question["question"])
                answers_list.append({
                    "id": question["id"],
                    "answer": answer
                })
            except Exception as e:
                print(f"Error for question {question}: ", e)

        return answers_list

    def handle_qestion(self, question: str, get_query_response):
        """
        Handles a single question and returns an answer.

        Parameters:
        - question: The question to be answered (string).
        - get_query_response: A function that takes a question (string) and returns an answer (string).

        Returns:
        - The answer to the question (string).
        """
        try:
            answer = get_query_response(question)
        except Exception as e:
            print(f"Error for question {question}: ", e)
            return "An error occurred while processing the question."
        return answer

    def get_rag_response_function(self, get_query_function):
        """
        Returns a function that handles HTTP requests to the RAG endpoint and returns a response.

        Parameters:
        - get_query_function: The function to get the query response.
        """
        def endpoint_function():
            """
            Handles HTTP requests to the RAG endpoint and returns a response.

            Expects a JSON payload containing either a 'questions' list, a 'question' string or a 'presets' dictionary.

            1) If a 'questions' list is provided, each question entry should have the following structure:
            {
                "id": <string>,  # Unique identifier for the question
                "question": <string>  # The question to be answered
            }
            Output:
            Returns a dictionary with 'answer' key containing a list of answers corresponding to the questions if a 'questions' list is provided.
            {
                "answer": [
                    {
                        "id": <string>,  # Unique identifier for the question
                        "answer": <string>  # The answer to the question
                    },
                    ...
            ]}

            2) If a 'question' string is provided, it will be answered directly.
            {
                "question": <string>  # The question to be answered
            }
            Output:
            Returns a dictionary with a 'answer' key containing a single answer if a 'question' string is provided.
            {
                "answer": <string>  # The answer to the question
            }

            3) If a 'presets' dictionary is provided, it should contain a 'history_accepted' boolean to toggle the history acceptance.
            {
                "presets": {
                    "history_accepted": <boolean>
                }
            }
            Returns a dictionary with 'response' and 'message' keys containing success message.
            Output:
            {
                "response": "Sucess",
                "message" : "History accepted: <boolean>"   
            }

            Returns:
            {"error": <string>}

            """
            try:
                data = request.get_json()
                
                # Check if the request contains a 'questions' list
                if "questions" in data:
                    questions_list = data.get('questions', [])

                    if "chat_history" in data and not self.history_accepted:
                        return jsonify({"error": "History is not accepted"}), 400

                    # Handle the list of questions
                    answers_list = self.handle_qestions_list(questions_list, get_query_function)
                    
                    # Return the answers as a JSON response
                    return jsonify({
                        "answer": answers_list
                    })

                # Check if the request contains a 'question' string
                elif "question" in data:
                    question = data.get('question', "")

                    if "chat_history" in data and not self.history_accepted:
                        return jsonify({"error": "History is not accepted"}), 400
                    
                    # Handle the single question
                    answer = self.handle_qestion(question, get_query_function)

                    # Return the answer as a JSON response
                    return jsonify({
                        "answer": answer
                    })

                # Check if the request contains a 'presets' dictionary
                elif "presets" in data:
                    presets_data = data.get('presets', {})
                    history_accepted = presets_data.get('history_accepted', "")

                    # Update the history acceptance status if the 'history_accepted' parameter is present
                    if history_accepted != "":
                        self.history_accepted = history_accepted
                    
                    # Return a success message as a JSON response
                    return jsonify({
                        "response": "Sucessfully updated",
                        "message" : f"History accepted: {self.history_accepted}"
                    })

                # If none of the above conditions are met, return an error message
                else:
                    return jsonify({"error": "Missing parameter."}), 400

            except Exception as e:  
                print(f"Error in {self.route}: ", e)
                return jsonify({"error": f"Error occured while processing the request"}), 500
        return endpoint_function

# Example usage
# if __name__ == "__main__":
#     # app object
#     app = Flask(__name__)

#     # temp anonymous function
#     get_query_response = lambda x: x

#     # Endpoint handler class
#     handler = LlmJudge()

#     # create endpoint
#     handler.create_rag_response_endpoint(app, get_query_response)
    
#     # local dev server
#     app.run(host="0.0.0.0", port=5000, use_reloader=True)
    