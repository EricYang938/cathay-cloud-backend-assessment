# API Reference

HTTP API v2，JSON UTF-8。除 GET `/health` 外需 `Authorization: Bearer <DEMO_TOKEN>`。錯誤為 `{"error":{"code":"...","message":"..."},"request_id":"..."}`，不包含底層錯誤。OPTIONS 僅接受允許的 origin。上游 API Gateway 產生的 429 / 5xx 可能使用平台錯誤格式。

| Method | Path | 成功 | 說明 |
|---|---|---|---|
| GET | /health | 200 | 程式存活檢查，**不代表 DynamoDB ready** |
| POST | /tasks | 201 | title 必填，description/status 選填；回傳完整物件 |
| GET | /tasks?limit=50&cursor=UUID | 200 | `items`、`next_cursor`；下一頁帶回 cursor；最多 100 |
| GET | /tasks/{UUID} | 200 | 完整 Task |
| PATCH | /tasks/{UUID} | 200 | title / description / status 至少一欄，回完整更新物件 |
| DELETE | /tasks/{UUID} | 204 | 空 body；重複刪除回 404 |
| GET | /weather?city=Taipei | 200 | geocoding 第一個同名結果；current、units、UTC、來源 |

Task：task_id UUID、title 1–200 字元（去首尾空白）、description 0–2000 字元、status TODO/IN_PROGRESS/DONE、created_at/updated_at UTC ISO 8601。禁止未知欄位、null 與其他型別；不能變更 ID / timestamps。JSON request body 最大 16 KiB。

| 狀態 | 情境 |
|---|---|
| 400 | JSON / 欄位 / UUID / 分頁 / 城市驗證失敗 |
| 401 | 缺少或錯誤展示權杖 |
| 403 | 本地 adapter 不允許來源的 preflight |
| 404 | 任務／路由／城市不存在 |
| 405 | 已知路由不支援 method |
| 413 | 本地/Lambda 本文超過 16 KiB |
| 429 | Gateway 節流；本地 adapter 無節流 |
| 500 | 未預期內部錯誤 |
| 502 | 天氣網路／HTTP／schema 錯誤 |
| 503 | 資料庫例外或 DEMO_TOKEN 未設定 |
| 504 | 天氣供應者逾時 |

```bash
curl "$API_URL/health"
curl -X POST "$API_URL/tasks" -H "Authorization: Bearer $DEMO_TOKEN" \
  -H 'Content-Type: application/json' -d '{"title":"Prepare interview","status":"TODO"}'
curl "$API_URL/tasks?limit=50" -H "Authorization: Bearer $DEMO_TOKEN"
curl "$API_URL/weather?city=Taipei" -H "Authorization: Bearer $DEMO_TOKEN"
```

天氣 API 每次請求 connect timeout 2 秒、read timeout 3 秒，沒有背景重試；外部兩次呼叫及網路環境仍影響整體延遲，Lambda 上限 20 秒。天氣是模型即時估計，非地面測站實測。官方免費介面適用非商業展示，需遵守當時授權與用量限制，商業使用另行確認。查詢使用者選擇的城市會傳送給 Open-Meteo，不傳送任務資料。
