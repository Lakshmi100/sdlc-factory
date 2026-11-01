# RETAIL-2: Products CRUD

Type: Story · Story points: 3 · Labels: products, medium, factory
Source: jira/stories.csv (row 2)

Implement create, read, update, delete and list for products, mirroring services/customers.

Acceptance criteria:
- Product fields: id, sku (unique), name, description (optional), price (decimal, > 0), created_at, updated_at
- Endpoints: POST /products, GET /products, GET /products/{id}, PUT /products/{id}, DELETE /products/{id}
- Duplicate sku returns 409; missing product returns 404; price <= 0 returns 422
- Tests cover every endpoint and every error case above
