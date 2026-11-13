"""Depuis fastapi_corrected/ : python -m unittest discover -s tests -v"""

import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from datas import users
from datas.security import verify_password
from main import app


INITIAL_USERS = [user.model_copy(deep=True) for user in users]


class TestFastAPIUsers(unittest.TestCase):
    def setUp(self):
        users[:] = [user.model_copy(deep=True) for user in INITIAL_USERS]
        self.client = TestClient(app)

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_get_all_users_has_pagination_and_no_password(self):
        response = self.client.get("/users?limit=2&offset=1")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual([user["name"] for user in result], ["Patoche", "Gontrand"])
        self.assertEqual(set(result[0]), {"name", "birthdate"})

    def test_get_one_user_has_no_password(self):
        response = self.client.get("/user/0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"name": "Gustave", "birthdate": "1990-05-14"})
        self.assertEqual(self.client.get("/users/0").json(), response.json())

    def test_invalid_ids(self):
        for path in ("/user/-1", "/user/20", "/user/abc"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 422 if path.endswith("abc") else 404)

    def test_invalid_pagination(self):
        self.assertEqual(self.client.get("/users?offset=-1").status_code, 422)
        self.assertEqual(self.client.get("/users?limit=-1").status_code, 422)

    def test_create_user(self):
        response = self.client.post("/user", json={
            "name": "Élodie-Rose", "password": "TrainingPass123!",
            "validation": "TrainingPass123!", "birthdate": "1991-04-12",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), 20)
        self.assertEqual(self.client.get("/user/20").json(), {
            "name": "Élodie-Rose", "birthdate": "1991-04-12",
        })
        self.assertTrue(verify_password("TrainingPass123!", users[20].password_hash))
        self.assertNotEqual(users[20].password_hash, "TrainingPass123!")

    def test_create_user_rejects_invalid_data(self):
        samples = [
            {"name": "Ana", "password": "short", "validation": "short", "birthdate": "1991-01-01"},
            {"name": "Ana", "password": "TrainingPass123!", "validation": "different", "birthdate": "1991-01-01"},
            {"name": "A", "password": "TrainingPass123!", "validation": "TrainingPass123!", "birthdate": "1991-01-01"},
            {"name": "Ana", "password": "TrainingPass123!", "validation": "TrainingPass123!", "birthdate": "2999-01-01"},
        ]
        for payload in samples:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/user", json=payload).status_code, 422)

    def test_patch_name_does_not_change_password(self):
        before = users[0].password_hash
        response = self.client.patch("/user/0", json={"name": "Gustave Martin"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"name": "Gustave Martin", "birthdate": "1990-05-14"})
        self.assertEqual(users[0].password_hash, before)

    def test_patch_password_requires_old_password_and_confirmation(self):
        endpoint = "/user/0/password"
        bad_old = {"old_password": "nope", "new_password": "NewPassword123!", "validation": "NewPassword123!"}
        self.assertEqual(self.client.patch(endpoint, json=bad_old).status_code, 400)
        mismatch = {"old_password": "Password123!", "new_password": "NewPassword123!", "validation": "Mismatch123!"}
        self.assertEqual(self.client.patch(endpoint, json=mismatch).status_code, 422)
        before = users[0].password_hash
        correct = {"old_password": "Password123!", "new_password": "NewPassword123!", "validation": "NewPassword123!"}
        response = self.client.patch(endpoint, json=correct)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertNotEqual(users[0].password_hash, before)
        self.assertTrue(verify_password("NewPassword123!", users[0].password_hash))
        self.assertFalse(verify_password("Password123!", users[0].password_hash))
        self.assertEqual(set(self.client.get("/user/0").json()), {"name", "birthdate"})

    def test_delete_returns_no_content(self):
        response = self.client.delete("/user/0")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(len(users), 19)
        self.assertEqual(self.client.get("/user/0").json()["name"], "Patoche")

    def test_edit_missing_user(self):
        self.assertEqual(self.client.patch("/user/999", json={"name": "Élodie"}).status_code, 404)
        self.assertEqual(self.client.patch("/user/999/password", json={
            "old_password": "unused", "new_password": "NewPassword123!", "validation": "NewPassword123!",
        }).status_code, 404)
        self.assertEqual(self.client.delete("/user/999").status_code, 404)

    def test_chat_uses_local_llm(self):
        async def fake_post(client, url, json):
            self.assertEqual(url, "http://127.0.0.1:8080/v1/chat/completions")
            self.assertEqual(json["messages"][0]["content"], "Bonjour")
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Salut"}}]},
                request=httpx.Request("POST", url),
            )

        with patch.dict("os.environ", {"LLM_BASE_URL": "http://127.0.0.1:8080/v1", "LLM_MODEL": "local"}), patch("main.httpx.AsyncClient.post", new=fake_post):
            response = self.client.post("/chat?prompt=Bonjour")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Salut"})


if __name__ == "__main__":
    unittest.main()
