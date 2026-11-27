# Shared Authorization Standard

Universal Dashboard Studio

Owner: PIC 1 - Core Backend & Integration

## Application Roles

- Admin
- Editor
- Viewer

Role names are case-sensitive.

Application roles are managed using Django Groups.

## Shared Authorization Decorator

All protected function-based HTML views must use
the shared role authorization decorator.

```python
from apps.accounts.decorators import role_required
```

## Admin Only

```python
@role_required("Admin")
def connection_view(request):
    ...
```

## Admin and Editor

```python
@role_required("Admin", "Editor")
def query_view(request):
    ...
```

## Dashboard Page Access

```python
@role_required("Admin", "Editor", "Viewer")
def dashboard_view(request):
    ...
```

## Access Matrix

| Module | Admin | Editor | Viewer |
| --- | --- | --- | --- |
| Overview | Yes | Yes | Yes |
| My Dashboards | Yes | Yes | Yes |
| Data Sources | Yes | No | No |
| Database Connections | Yes | No | No |
| Database Explorer | Yes | No | No |
| Data Manager | Yes | Yes | No |
| Query Builder | Yes | Yes | No |
| Visualization Builder | Yes | Yes | No |
| Templates | Yes | Yes | No |
| Settings | Yes | No | No |

## Response Behavior

- Unauthenticated users are redirected to login.
- Unauthorized users receive HTTP 403.
- Authorized users can execute the protected view.
- Active superusers have the Admin application role.
- Users without application roles are denied access.

## Development Rules

- Do not implement separate role systems.
- Do not rely only on hidden frontend menus.
- Authorization must be enforced on the backend.
- Do not expose database credentials.
- Do not grant superuser permissions to normal users.
- Coordinate authorization changes with PIC 1.

## Current Limitations

The decorator provides page-level role authorization
for synchronous Django function-based HTML views.

Object-level permissions must be checked separately.

Dashboard access does not grant permission to view
every dashboard or its underlying datasets.

Viewer access must remain read-only.

JSON API endpoints require separate API authorization
and standardized HTTP 401 and 403 responses.

Object-level permissions and API authorization
will be implemented in subsequent development stages.