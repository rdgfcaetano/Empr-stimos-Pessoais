from datetime import date, timedelta

from conftest import login


def test_partner_cannot_access_other_partner_records(client):
    partner_a = login(client, "a@test")
    partner_b = login(client, "b@test")

    created = client.post("/api/clients", headers=partner_a, json={"name": "Cliente A", "phone": "111"}).json()
    blocked = client.put(f"/api/clients/{created['id']}", headers=partner_b, json={"name": "Invasao"})

    assert blocked.status_code == 404
    visible_to_b = client.get("/api/clients", headers=partner_b).json()
    assert visible_to_b == []


def test_payment_marks_loan_paid_and_creates_notification(client):
    admin = login(client, "admin@test", "Admin123!")
    partner = login(client, "a@test")
    client_id = client.post("/api/clients", headers=partner, json={"name": "Maria", "phone": "222"}).json()["id"]
    loan = client.post(
        "/api/loans",
        headers=partner,
        json={
            "client_id": client_id,
            "principal": "100.00",
            "interest_rate": "0",
            "interest_type": "monthly",
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=10)),
            "late_fee": "0",
            "late_interest_rate": "0",
        },
    ).json()

    payment = client.post(
        f"/api/loans/{loan['id']}/payments",
        headers=partner,
        json={"paid_at": str(date.today()), "amount": "100.00", "notes": "quitacao"},
    )

    assert payment.status_code == 200
    loans = client.get("/api/loans", headers=partner).json()
    assert loans[0]["status"] == "paid"
    notifications = client.get("/api/notifications", headers=admin).json()
    assert any("Pagamento" in n["title"] for n in notifications)


def test_admin_can_see_logs_but_partner_cannot(client):
    admin = login(client, "admin@test", "Admin123!")
    partner = login(client, "a@test")

    assert client.get("/api/logs", headers=admin).status_code == 200
    assert client.get("/api/logs", headers=partner).status_code == 403
