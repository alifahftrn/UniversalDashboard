# Universal Dashboard Studio

## API & Dataset Contract v1

Reference: RFC v2.3 Final, Section 16 and 17.

## Planned API Endpoints

| Method | Endpoint | Owner |
| --- | --- | --- |
| GET | /api/v1/datasets/ | PIC 3 |
| POST | /api/v1/extractions/ | PIC 2 |
| GET | /api/v1/jobs/{id}/ | PIC 2 |
| POST | /api/v1/queries/preview/ | PIC 3 |
| POST | /api/v1/dashboards/ | PIC 4 |
| GET | /api/v1/dashboards/{id}/ | PIC 4 |
| PATCH | /api/v1/dashboards/{id}/ | PIC 4 |

## Shared Rules

- API responses use JSON UTF-8.
- Public identifiers use UUID.
- Timestamps use ISO 8601 UTC.
- Decimal values use strings.
- Missing values use null.
- External databases are read-only.
- Source access is restricted to authorized
  connection and extraction operations.
- Analytics queries use internal datasets only.
- Dashboard refresh must not trigger extraction.
- Authentication and ownership checks are required.
- Mutating requests require CSRF protection
  when using Django session authentication.
- Never expose database credentials.
- Never expose physical dataset table names.

## Fixtures

- raw_demo.csv
- validated_demo.json
- query_result.json

All fixtures contain synthetic data.

## Contract Changes

Changes must be reviewed by the producer,
consumer, and PIC 1 before merging.

## Implementation Status

These contracts are proposed integration
examples. Endpoints are not implemented yet.