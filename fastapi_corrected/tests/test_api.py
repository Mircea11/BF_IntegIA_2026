"""Run: python -m unittest discover -s tests -v"""
import unittest

from fastapi.testclient import TestClient

from datas import users
from main import app


class FastAPITrainingTests(unittest.TestCase):
    def setUp(self):
        # Reset the in-memory data so tests are independent.
        users[:] = ["John Doe", "Jane Smith", "Bob Johnson"]
        self.client = TestClient(app)

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["documentation"], "/docs")

    def test_get_all_users(self):
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["John Doe", "Jane Smith", "Bob Johnson"])

    def test_get_valid_user(self):
        response = self.client.get("/users/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Jane Smith")

    def test_get_invalid_user_id(self):
        for url in ("/users/-1", "/users/3"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "User not found"})

    def test_get_noninteger_id(self):
        response = self.client.get("/users/abc")
        self.assertEqual(response.status_code, 422)

    def test_post_user_and_read_back(self):
        response = self.client.post("/user", json={"name": "Ana"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), 3)
        self.assertEqual(self.client.get("/users/3").json(), "Ana")

    def test_post_duplicate_name_returns_new_id(self):
        response = self.client.post("/user", json={"name": "John Doe"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), 3)  # Not the first matching name's ID (0)

    def test_post_invalid_body(self):
        for payload in ({}, {"name": ""}):
            response = self.client.post("/user", json=payload)
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
