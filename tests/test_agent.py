import requests

BASE_URL = "http://127.0.0.1:8000/agent"

test_queries = [
    "show products",
    "what products do you have",
    "where is my order 1001",
    "check order 1002",
    "cancel order 1001",
    "please cancel my order 1002",
    "what store is this",
    "hello",
    "where is my order 9999"
]

def test_agent_queries():
    for query in test_queries:
        print(f"\nTesting query: {query}")

        response = requests.post(BASE_URL, params={"query": query})
        data = response.json()

        print("Response:", data)

        assert response.status_code == 200