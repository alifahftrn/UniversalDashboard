# Universal Dashboard Studio — API Standard v1

Owner: PIC 1 (Core, Security & Integration)  
Status: baseline implementasi ditetapkan PIC 1; review kompatibilitas producer/consumer sebelum merge. Belum merupakan API aktif.  
Referensi: RFC v2.3 Final §16–17; dataset-v1.json, query-v1.json, errors-v1.json, README.md; panduan integrasi PIC 2 dan PIC 3.

## 1. Keputusan kontrak

- Semua endpoint publik berprefix `/api/v1/`, dengan trailing slash. JSON UTF-8, UUID publik, timestamp UTC ISO 8601 (akhiran `Z`), decimal berupa string, nilai kosong `null`. NaN dan Infinity dilarang.
- Success body mengikuti resource langsung, tanpa envelope `success`/`data`. Error hanya envelope `error` dengan `code`, `message`, `request_id`. `request_id` adalah UUID per request yang dibuat server; header `X-Request-ID` pada respons API menggunakan nilai sama. Jangan percaya ID dari client.
- Nama kolom `key`, agregasi `group_by`, `measures[].column/op/alias`, serta `version_id` dipertahankan. Query result memakai `rows` berupa array dari array, sesuai urutan `columns`. Tidak ada `dataset_id` tambahan pada query result baseline.
- Schema formal: `openapi-v1.yaml` (OpenAPI 3.1). File contoh JSON lama dipertahankan. Bila ada perbedaan dengan dokumen panduan lama yang masih berupa usulan, gunakan baseline ini setelah review kompatibilitas.

## 2. Endpoint dan kepemilikan

| Method | Path | Owner | Success |
| --- | --- | --- | --- |
| GET | /api/v1/datasets/ | PIC 3 | 200, daftar metadata versi aktif |
| POST | /api/v1/extractions/ | PIC 2 | 202, job_id dan status queued |
| GET | /api/v1/jobs/{id}/ | PIC 2 | 200, status JobRun |
| POST | /api/v1/queries/preview/ | PIC 3 | 200, hasil query internal |
| POST | /api/v1/dashboards/ | PIC 4 | 201, dashboard |
| GET | /api/v1/dashboards/{id}/ | PIC 4 | 200, dashboard |
| PATCH | /api/v1/dashboards/{id}/ | PIC 4 | 200, dashboard setelah perubahan |

Endpoint tambahan tidak ditetapkan sendiri. PIC 1 mengelola prefix/routing induk; tiap PIC mengelola urls dan views domain masing-masing. Service tidak bergantung pada HttpRequest, template atau response HTTP. Shared API utilities diletakkan di `apps/core/api/` sesuai rancangan starter saat ini; jangan membuat duplikat di setiap app.

## 3. Authentication, CSRF dan permission

- Django session authentication (cookie `sessionid` dan header `X-CSRFToken` untuk POST/PATCH; nama default Django, sesuaikan konfigurasi bersama bila berubah). Cookie same-origin; jangan membuka CORS untuk MVP. POST query preview juga wajib CSRF meskipun read-only secara data.
- API tidak redirect ke halaman login. Anonymous pada pemeriksaan autentikasi mendapat 401 JSON; CSRF failure mendapat 403 JSON, termasuk jika middleware menolak sebelum view. Middleware/handler harus menangani 404, 405, 500 serta error CSRF dalam bentuk JSON pada prefix API. Error HTML di luar prefix tetap berlaku.
- `role_required` HTML yang sudah ada tidak digunakan sebagai pengganti decorator API. Role Admin, Editor, Viewer mengikuti `apps/accounts/access.py`; user nonaktif/no-role ditolak.
- MVP: Admin/Editor dapat list dataset dan preview query pada dataset yang diizinkan. Extraction dan job status hanya Admin dengan izin terhadap source/dataset/job. Create/PATCH dashboard: Admin/Editor berizin. GET dashboard: Admin/Editor/Viewer hanya pada dashboard milik sendiri atau yang diberikan akses. Viewer tidak mendapat endpoint query preview bebas; rendering dashboard Viewer menggunakan jalur server-side yang memeriksa dashboard/widget dan dataset binding. Endpoint khusus rendering Viewer akan ditetapkan terpisah; jangan memberi akses query generik sebagai jalan pintas.
- Default deny. Resource scope diturunkan dari user/session dan aturan ownership/sharing server, bukan role atau user_id kiriman client. Active superuser mengikuti kebijakan akses yang disepakati; jangan menganggap role Admin otomatis berhak pada setiap dataset. Untuk MVP tanpa model sharing, owner-only bagi user biasa; active superuser boleh akses administratif melalui kebijakan eksplisit dan audit. Untuk resource ID tidak ada atau tidak berizin: 404 (mencegah enumerasi); role tidak sesuai: 403. Akses dataset di dashboard wajib diperiksa juga.
- Recheck izin sebelum query/cache hit, download atau eksekusi job. Endpoint data nyata belum boleh diaktifkan sebelum object authorization tersedia.

## 4. Payload dan semantik

### Dataset list

`GET /api/v1/datasets/?page=1&page_size=20` mengembalikan `{ "count": 1, "page": 1, "page_size": 20, "results": [ ... ] }`. Setiap item mengikuti `dataset-v1.json` dan hanya active version tervalidasi. `page_size` default 20, maksimum 100; urutan dataset_id deterministik. Dataset tanpa versi aktif tidak ditampilkan di endpoint analitik ini; UI pengelolaan metadata belum memiliki kontrak publik terpisah. `count` hanya menghitung resource berizin.

### Extraction

POST body `{ "source_id": "<uuid>", "dataset_id": "<uuid>" }`. Source dan dataset harus cocok dengan definisi selection/recipe yang tersimpan dan berizin. Client tidak mengirim credential, SQL bebas atau nama tabel fisik. Mode full untuk MVP; incremental menyusul setelah semantics watermark/update/delete teruji. JobRun dibuat secara durabel sebelum 202. Jika target sudah punya job queued/running, 409 `JOB_CONFLICT`; locking wajib atomik. Retry worker memakai job_id/batch key yang sama; request POST baru setelah job terminal adalah refresh baru. `job_id` publik merujuk JobRun (bukan definisi jadwal).

GET job mengembalikan job_id, dataset_id, status, row_count (jumlah baris yang berhasil di-ingest untuk run, tidak sama dengan jumlah tervalidasi), error_code, created_at, started_at, finished_at, version_id (versi validated hasil run jika sukses, null sebelum sukses). Success hanya setelah publish atomik selesai; failed tidak mengubah pointer terakhir. Waktu belum tersedia dan error_code tanpa error adalah null. Status: queued/running/success/failed.

### Query preview

Request mengikuti `query-v1.json`; optional `version_id` merupakan perluasan kompatibel untuk pin versi validated yang berizin, jika tidak ada server resolve active version sekali. Default limit 100; 1–10.000. `group_by` boleh kosong, `measures` minimal 1 untuk preview agregat MVP. Operator awal: sum, avg, count, count_distinct, min, max. Count menghitung non-null; sum/avg hanya tipe numerik. Alias unik dan tidak bentrok dengan key group_by. Filter MVP: list AND, `{column, op, value}`; eq, ne, gt, gte, lt, lte, in, is_null, is_not_null. `in` memakai array nonkosong; null check tidak membawa value, operator lain tidak menerima null. Validasi tipe mengikuti metadata, bukan casting diam-diam. Request invalid mendapat 400, termasuk key/operator yang tidak dikenal.

Query result: `version_id`, `columns` (key, type), `rows`, `truncated`, `last_extracted_at`. Urutan row mengikuti group_by secara deterministik, null terakhir. `truncated=true` bila terdapat lebih banyak result row dari limit (deteksi limit+1), bukan jumlah raw row. Agregasi atas seluruh subset berizin setelah filter, bukan agregasi atas preview terpotong. Jangan gunakan hasil truncated sebagai KPI total tanpa indikasi.

### Dashboard

MVP create: `name`, `widgets` (default []); GET/PATCH response menambahkan `dashboard_id`. PATCH partial untuk name/widgets; penggantian widgets bersifat utuh dan atomik. Widget minimal: `type`, `dataset_id`, `query_config` (group_by, measures, filters, limit), `binding` (x/y key hasil query; boleh null bila tidak relevan), `layout` (x,y,w,h). Type awal bar, line, pie, table, kpi. Draft layout/config tambahan, widget UUID, theme dan template di luar kontrak MVP ini. Server validasi layout, binding, akses seluruh dataset dan query config sebelum save. Ownership tidak dapat diubah lewat body. Konflik versi/edit yang terdeteksi 409; strategi optimistic locking detail menyusul sebelum multi-editor.

## 5. Error dan HTTP

| HTTP | Kode awal / arti |
| --- | --- |
| 200 / 201 / 202 | success / created / queued |
| 400 | INVALID_REQUEST, INVALID_COLUMN, INVALID_FILTER, INVALID_AGGREGATION |
| 401 | AUTHENTICATION_REQUIRED |
| 403 | PERMISSION_DENIED, CSRF_FAILED |
| 404 | NOT_FOUND |
| 405 | METHOD_NOT_ALLOWED (header Allow) |
| 409 | JOB_CONFLICT, VERSION_CONFLICT |
| 422 | VALIDATION_FAILED (request sah tetapi aturan proses tidak terpenuhi) |
| 429 | RATE_LIMITED (Retry-After bila diketahui) |
| 500 | INTERNAL_ERROR |
| 503 | SERVICE_UNAVAILABLE |

Contoh: `{"error":{"code":"INVALID_COLUMN","message":"Kolom tidak valid","request_id":"00000000-0000-4000-8000-000000000003"}}`. Jangan kirim credential, stack trace, SQL internal, physical table name atau isi data sensitif dalam error/log. Semua method tidak didukung harus mengembalikan 405; OPTIONS/HEAD bila dibutuhkan harus ditetapkan eksplisit, tanpa efek mutasi.

## 6. Testing dan perubahan kontrak

Unit test per domain dan contract/integration test lintas PIC: fixture lama valid terhadap schema, anonymous/role/ownership/CSRF, method/error envelope, limit/timeout, cache scope, retry tanpa duplikasi, publish gagal tidak mengganti active version, serta source offline setelah publish (query/dashboard tetap berfungsi). OpenAPI hanya validasi bentuk; izin, tipe kolom dinamis, lineage dan invariant perlu test perilaku.

Breaking change: diskusikan producer + consumer + PIC 1; revisi schema, fixture, test, dan bila perlu versi API. PR harus CI hijau dan review sesuai aturan tim. Jangan menandai endpoint aktif sebelum implementasi & security tests lulus. Keputusan MVP tambahan di atas belum merupakan bukti persetujuan anggota lain.
