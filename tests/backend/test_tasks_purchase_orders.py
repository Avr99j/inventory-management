"""
Tests for task and purchase order API endpoints.
"""
import pytest


class TestTasksEndpoints:
    """Test suite for task endpoints (in-memory)."""

    def test_get_tasks(self, client):
        """Test getting tasks returns a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client):
        """Test creating a task returns a pending task with a prefixed ID."""
        payload = {"title": "Review Q4 stock", "priority": "high", "dueDate": "2025-10-08"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201

        task = response.json()
        assert task["id"].startswith("task-")
        assert task["title"] == "Review Q4 stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-08"
        assert task["status"] == "pending"

        # Newly created task appears in the list, newest first
        tasks = client.get("/api/tasks").json()
        assert tasks[0]["id"] == task["id"]

    def test_create_task_invalid_priority(self, client):
        """Test creating a task with an unknown priority is rejected."""
        response = client.post(
            "/api/tasks",
            json={"title": "Bad priority", "priority": "urgent", "dueDate": "2025-10-08"}
        )
        assert response.status_code == 400

    def test_create_task_missing_title(self, client):
        """Test creating a task without a title fails validation."""
        response = client.post("/api/tasks", json={"title": "", "dueDate": "2025-10-08"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test toggling a task flips pending and completed."""
        task = client.post(
            "/api/tasks",
            json={"title": "Toggle me", "priority": "low", "dueDate": "2025-10-09"}
        ).json()

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task = client.post(
            "/api/tasks",
            json={"title": "Delete me", "priority": "medium", "dueDate": "2025-10-10"}
        ).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200

        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert task["id"] not in ids

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints (in-memory)."""

    @pytest.fixture
    def backlog_item_without_po(self, client):
        """Find a backlog item that doesn't have a purchase order yet."""
        items = client.get("/api/backlog").json()
        candidates = [item for item in items if not item["has_purchase_order"]]
        assert len(candidates) > 0, "No backlog item available without a purchase order"
        return candidates[0]

    def _payload(self, backlog_item_id):
        return {
            "backlog_item_id": backlog_item_id,
            "supplier_name": "Acme Components",
            "quantity": 350,
            "unit_cost": 12.5,
            "expected_delivery_date": "2025-11-15",
            "notes": "Rush order"
        }

    def test_create_and_get_purchase_order(self, client, backlog_item_without_po):
        """Test creating a purchase order, fetching it, and the backlog flag updating."""
        item_id = backlog_item_without_po["id"]

        response = client.post("/api/purchase-orders", json=self._payload(item_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == item_id
        assert po["supplier_name"] == "Acme Components"
        assert po["quantity"] == 350
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["status"] == "Pending"
        assert po["notes"] == "Rush order"

        response = client.get(f"/api/purchase-orders/{item_id}")
        assert response.status_code == 200
        assert response.json()["id"] == po["id"]

        # Backlog endpoint should now report the purchase order
        items = client.get("/api/backlog").json()
        updated = next(item for item in items if item["id"] == item_id)
        assert updated["has_purchase_order"] is True

    def test_create_duplicate_purchase_order(self, client, backlog_item_without_po):
        """Test a second purchase order for the same backlog item is rejected."""
        item_id = backlog_item_without_po["id"]
        assert client.post("/api/purchase-orders", json=self._payload(item_id)).status_code == 201

        response = client.post("/api/purchase-orders", json=self._payload(item_id))
        assert response.status_code == 409
        assert "already has" in response.json()["detail"].lower()

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test creating a purchase order for a missing backlog item."""
        response = client.post("/api/purchase-orders", json=self._payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_validation(self, client):
        """Test non-positive quantity and unit cost fail validation."""
        bad_quantity = self._payload("1")
        bad_quantity["quantity"] = 0
        assert client.post("/api/purchase-orders", json=bad_quantity).status_code == 422

        bad_cost = self._payload("1")
        bad_cost["unit_cost"] = -1
        assert client.post("/api/purchase-orders", json=bad_cost).status_code == 422

    def test_get_nonexistent_purchase_order(self, client):
        """Test getting a purchase order that doesn't exist."""
        response = client.get("/api/purchase-orders/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
