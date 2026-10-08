def register_and_login(client, email="priya@test.com", password="abc12345"):
    client.post("/register", json={"name": "Test", "email": email, "password": password})
    res = client.post("/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def add_food_category(client, headers):
    return client.post("/categories", json={"name": "Food"}, headers=headers).json()


def test_register_duplicate_email(client):
    body = {"name": "Priya", "email": "priya@test.com", "password": "abc12345"}
    assert client.post("/register", json=body).status_code == 200
    assert client.post("/register", json=body).status_code == 400


def test_login_wrong_password(client):
    client.post("/register", json={"name": "Priya", "email": "priya@test.com", "password": "abc12345"})
    res = client.post("/login", json={"email": "priya@test.com", "password": "wrong"})
    assert res.status_code == 401


def test_expenses_need_login(client):
    res = client.get("/expenses")
    assert res.status_code in (401, 403)


def test_add_and_list_expense(client):
    headers = register_and_login(client)
    cat = add_food_category(client, headers)

    body = {"amount": 480, "category_id": cat["id"], "note": "Zomato dinner", "date": "2026-10-05"}
    res = client.post("/expenses", json=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["amount"] == 480

    listing = client.get("/expenses?month=2026-10", headers=headers).json()
    assert len(listing) == 1


def test_user_cannot_see_or_delete_other_users_data(client):
    priya = register_and_login(client, "priya@test.com")
    rahul = register_and_login(client, "rahul@test.com")

    cat = add_food_category(client, priya)
    body = {"amount": 100, "category_id": cat["id"], "date": "2026-10-05"}
    expense = client.post("/expenses", json=body, headers=priya).json()

    assert client.get("/categories", headers=rahul).json() == []
    assert client.get("/expenses", headers=rahul).json() == []
    assert client.delete(f"/expenses/{expense['id']}", headers=rahul).status_code == 404


def test_budget_warning_then_exceeded(client):
    headers = register_and_login(client)
    cat = add_food_category(client, headers)
    client.post(
        "/budgets",
        json={"category_id": cat["id"], "month": "2026-10", "limit": 1000},
        headers=headers,
    )

    client.post(
        "/expenses",
        json={"amount": 850, "category_id": cat["id"], "date": "2026-10-05"},
        headers=headers,
    )
    status = client.get("/budgets/status?month=2026-10", headers=headers).json()[0]
    assert status["status"] == "warning"

    client.post(
        "/expenses",
        json={"amount": 200, "category_id": cat["id"], "date": "2026-10-06"},
        headers=headers,
    )
    status = client.get("/budgets/status?month=2026-10", headers=headers).json()[0]
    assert status["status"] == "exceeded"


def test_monthly_summary(client):
    headers = register_and_login(client)
    cat = add_food_category(client, headers)
    client.post(
        "/budgets",
        json={"category_id": cat["id"], "month": "2026-10", "limit": 1000},
        headers=headers,
    )
    client.post(
        "/expenses",
        json={"amount": 300, "category_id": cat["id"], "date": "2026-10-05"},
        headers=headers,
    )

    summary = client.get("/reports/summary?month=2026-10", headers=headers).json()
    assert summary["total_spent"] == 300
    assert summary["total_budget"] == 1000
    assert summary["remaining"] == 700
    assert summary["expense_count"] == 1