# Universal Dashboard Studio — Data Pipeline Standard v1

Owner: PIC 1; implementasi PIC 2 dan PIC 3, consumer PIC 4.  
Baseline implementasi MVP; review kompatibilitas lintas PIC sebelum merge. Referensi RFC v2.3 §02, §06, §09, §16 dan panduan integrasi PIC 2/3.

## 1. Jalur data dan batas tanggung jawab

`External source → PIC 2 connector/worker → PIC 3 storage(raw) → staging → validation → validated/quarantine → internal query/cache → PIC 4 dashboard`.

| PostgreSQL schema | Pemilik operasi | Aturan |
| --- | --- | --- |
| app | tiap PIC sesuai domain | metadata Django ORM, search_path=app; migrations metadata |
| raw | PIC 3 storage; PIC 2 pengirim batch | snapshot sumber disegel immutable; tidak diedit engine |
| staging | PIC 3 | versi kerja, transformasi |
| validated | PIC 3 | versi lulus aturan, immutable setelah publish |
| quarantine | PIC 3 | row gagal, reason/rule, lineage; akses terbatas |

PIC 2 hanya source metadata/test/preview terbatas/extraction; koneksi sumber read-only dengan akun yang tidak memiliki izin tulis, allowlist target dan timeout. PIC 3 tidak membuka koneksi eksternal. PIC 4 hanya query/cache internal. Refresh, filter, cache expired, export tidak boleh memicu connector/extraction.

Nama fisik tabel dibuat server dan schema-qualified; jangan terima identifier fisik mentah dari client, jangan kirim ke browser. Django migration mengelola metadata; dynamic physical storage dikelola service. Jangan menambah tabel fact/dim wajib karena dataset dinamis. Peran read-only terpisah untuk query internal, tanpa akses raw/staging/quarantine kecuali service yang memang berwenang; enforce dataset scope selain grant DB. Jangan menggunakan kredensial app owner untuk custom SQL.

## 2. Service interface lintas PIC

Nama dasar mengikuti RFC; keyword batch key dan seal merupakan keputusan implementasi tambahan untuk memenuhi idempotensi/raw immutable. Signature ini adalah kontrak Python yang disepakati sebagai target, bukan fungsi yang sudah tersedia.

```python
connector.read_batches(source_id, selection)
storage.begin_version(dataset_id, job_id, columns)
storage.write_batch(version_id, rows, *, batch_key)
storage.seal_raw(version_id)
pipeline.run(version_id, recipe_id)
storage.publish(version_id)
```

- Connector PIC 2 mengembalikan `columns` dan iterator batch berurutan; `selection` berasal dari konfigurasi sumber berizin yang tersimpan, bukan SQL dari client. Batch berisi row array/list sesuai urutan columns. Nilai mengikuti tipe kanonis; pada boundary JSON decimal string, date/datetime ISO, null. Ingest nilai invalid yang masih dapat direpresentasikan sebagai data mentah untuk validasi; jangan silently cast atau buang baris. Kesalahan struktur batch gagal run.
- Begin version PIC 3 membuat metadata versi kerja berstatus `staging` dan raw ingest area privat. Source/job/recipe ditelusuri dari metadata yang dibekukan untuk run. Versi raw ditandai `raw` setelah `seal_raw`; raw immutable setelah seal (termasuk tidak menambah batch). Area ingest belum disegel tidak boleh menjadi sumber analitik.
- Batch key deterministik `job_id:batch_index` (index mulai 0); unique per versi, payload checksum internal. Batch ledger + write rows dalam transaksi yang sama. Key dan checksum sama adalah no-op sukses; key sama payload berbeda adalah konflik dan run gagal. Retry hanya bila batch identik dapat direproduksi; jika stream berubah, fail run dan jalankan job baru. Jangan mengklaim exactly-once sumber tanpa snapshot konsisten.
- `pipeline.run` membaca raw yang sudah disegel dan membuat kandidat versi staging baru dengan lineage ke raw. Transform, validation, quarantine; hasil berupa ID kandidat versi. Tidak mengubah raw atau active version. Kandidat lulus aturan yang dikonfigurasi dapat diterbitkan. Invalid rows masuk quarantine; critical rule failure atau tidak memenuhi acceptance policy gagal run, bukan publish parsial tanpa indikator.
- `storage.publish` memverifikasi kandidat, izin dan job lock; materialisasi validated dan pindah active pointer dalam transaksi atomik yang konsisten dengan status JobRun sukses. Cache invalidation setelah commit (version_id dan izin tetap diperiksa sehingga cache lama tidak terbaca sebagai active). Versi sukses lama tetap tersedia sesuai kebijakan retention. Jika gagal, pointer tetap lama; kandidat failed dan partial storage di-cleanup terkontrol.

## 3. Metadata, status dan lineage

| Entitas | Minimum |
| --- | --- |
| Dataset | dataset_id UUID, owner/scope, source_id, active_version_id nullable, selection/recipe ref |
| DatasetVersion | version_id UUID, dataset_id, parent/raw version reference, job_id, columns, status, row_count, last_extracted_at |
| JobRun | job_id UUID, dataset_id, source_id, status, row_count, error_code, created/started/finished timestamps, version_id nullable |
| Quarantine entry | job_id, version reference, row reference, rule/error, restricted raw value where necessary |

Job: queued → running → success/failed; queued boleh failed jika dispatch gagal. Version: staging (ingest) → raw; kandidat staging terpisah → validated/failed. Hanya validated yang bisa menjadi active. Row count raw = seluruh row yang diterima, validated = row hasil transform yang diterbitkan, quarantine = row/issue gagal (jumlah issue bisa lebih besar dari row). Simpan metrik pada tiap tahap; join/agregasi bisa mengubah jumlah baris. Timestamps UTC, `last_extracted_at` merepresentasikan waktu selesai source extraction, bukan render time.

## 4. Scheduling, lock, failure

MVP: Django management command + OS scheduler. Job request/scheduler membuat JobRun durabel; worker mengambil queued secara atomik. Satu job queued/running per dataset (transactional lock/constraint); scheduler tidak membuat duplikat saat job aktif. Scheduler menggunakan service identity/konfigurasi scope yang disetujui dan audit; recheck izin/source sebelum eksekusi. Worker tidak menerima credential dari API payload. Retry hanya untuk transient failure, default maksimum 3 total percobaan dengan bounded backoff; fail stale job melalui mekanisme lease/recovery yang aman, jangan publish dari worker kehilangan lease. Sumber offline tidak memengaruhi versi aktif. Full extraction MVP; incremental belum aktif sampai watermark/update/delete/retry semantics disepakati.

## 5. Batas resource awal (development/test)

| Kontrol | Nilai awal |
| --- | --- |
| Source explorer preview | max 500 rows (RFC) |
| Query preview | default 100; max 10.000 rows (RFC max) |
| Pandas JOIN | max 50.000 rows/input (RFC); max 100.000 output rows |
| Extraction batch | default max 1.000 rows dan 4 MiB payload per batch; split batch, fail jika satu row melampaui batas |
| Join memory guard | max 128 MiB total input/output estimasi, ukur deep memory; prefer SQL internal untuk data besar |
| Internal query statement timeout | 30 detik |
| External connect / read statement timeout | 10 / 60 detik, adapter-specific |
| Cache TTL | 300 detik; key = version_id + normalized query + access scope |
| JSON request body | 1 MiB untuk endpoint JSON v1; file upload memiliki policy tersendiri |

Batas ini default pengujian tambahan (bukan SLA produksi); konfigurasi server boleh diperketat. Limit preview tidak membatasi raw extraction diam-diam. Extraction volume/window, file upload, quota, retention, concurrency global, total runtime dan resource hard cap perlu kebijakan admin sebelum produksi; bila tidak terkonfigurasi jangan membuka job produksi. Timeout per statement bukan batas total job; worker harus punya deadline/lease. Jangan mengandalkan estimasi memory sebagai satu-satunya proteksi; hindari materialisasi join tak terbatas, guard output sebelum alokasi dan gunakan proses berlimit. Jangan silent truncation pada dataset/KPI.

## 6. Security dan test acceptance

SQL parameterized untuk nilai, allowlist kolom/tabel/op, parser/guard untuk custom SQL dan role read-only; SELECT/WITH saja tidak cukup. Formula parser AST whitelist, tanpa eval/exec. Credential terenkripsi via PIC 1, tidak disimpan di log/fixture. Cache cek akses sebelum hit; scope berubah invalidate. Audit job, publish, akses sensitif; raw/quarantine tunduk izin dan retention.

Wajib test: source read-only; schema mapping; raw immutable; batch retry identik/conflict; seal/pipeline/publish; dua concurrent jobs; worker crash/retry; failed validation/extraction mempertahankan active pointer; lineage/count; denied access/cache; query/filter/refresh/export saat source offline. Demo fixture: valid 3 rows, A=500000.00 dan B=1200000.00 sesuai RFC; cocokkan fixture repository aktual sebelum assertion final.

## 7. Handoff dan perubahan

PIC 2 → PIC 3: source_id, dataset_id, job_id, columns, iterator batch, batch_key. PIC 3 → PIC 2: candidate/validated version_id dan hasil run; PIC 3 → PIC 4: dataset metadata dan query result sesuai OpenAPI. PIC 1: API utility/auth/ownership/CI; review storage boundary dan keamanan. Ubah interface/kontrak hanya setelah producer, consumer, PIC 1 review; update test dan fixtures. Semua endpoint/data service ini target implementasi, bukan klaim sudah berjalan.
