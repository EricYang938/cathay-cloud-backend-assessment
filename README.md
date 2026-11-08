# Cloud Task Management System

國泰金控「雲端技術暨專案實習生」實作：Python 3.12 分層後端、AWS Serverless 架構、任務 CRUD 與輕量瀏覽器介面。應用於管理團隊示範工作事項，並查詢城市天氣，**不處理真實金融客戶資料**。

> 交付狀態：本地測試與 SAM 驗證／建置通過；AWS 尚未部署，GitHub 遠端尚未建立／更新。可使用 ZIP 交付。這是共享 Demo，沒有多使用者資料隔離。

## 功能與技術

- 建立、查詢、分頁列出、更新與刪除任務；狀態 TODO / IN_PROGRESS / DONE。
- DynamoDB 真實 SDK 存取，條件式更新／刪除、UUID、UTC timestamps、輸入驗證及安全錯誤回應。
- HTML/CSS/JavaScript 響應式前端，CRUD、loading、錯誤訊息；呼叫 API 而非固定 JSON。
- Open-Meteo geocoding → current weather，timeout 與錯誤隔離；本次外網實測逾時，mock 測試通過。
- AWS Lambda、API Gateway HTTP API、DynamoDB、IAM、CloudWatch，AWS SAM IaC。
- pytest、Moto HTTP emulator、Ruff、GitHub Actions CI 與預設停用的 OIDC CD。

## System Architecture

![AWS serverless architecture](docs/architecture.png)

瀏覽器 → HTTPS API Gateway → Python Lambda → DynamoDB；Lambda 對外呼叫天氣 API，CloudWatch 記錄狀態與延遲，IAM 限制資料表／日誌存取。圖中 AWS 資源為設計架構，**未宣稱已部署**。前端目前本地執行。

### AWS Service Selection

| 選型 | 原因 | 限制／取捨 |
|---|---|---|
| Lambda vs EC2 | 本題為短時間低流量請求，免管理 OS、隨用計費 | 冷啟動、執行時限與依賴大小限制；EC2 適合持續長連線／OS 控制 |
| DynamoDB vs RDS | UUID 鍵值 CRUD、按需容量、不需 JOIN | Scan 不適合大型搜尋；關聯查詢／多表交易可考慮 RDS |
| API Gateway | HTTPS、路由整合、CORS、節流、access logs | 另計請求費，平台錯誤可能不同於應用 JSON |
| Serverless | 降低閒置與維運負擔，託管擴展 | 供應商依賴、除錯跨服務、冷啟動與配額限制 |

預算與維運：不使用 EC2、RDS、NAT Gateway；表按需計費、日誌保留 14 天。以低量 Demo US$5/月作規劃假設，非報價與金額上限。大量 Scan、日誌、外網及流量仍產生成本，部署前使用 AWS Pricing Calculator。擴充時改為每使用者 Query/GSI、加入 JWT 與資源授權；目前以 concurrency 2、API 5 req/s／burst 10 控制展示規模。[完整設計理由](docs/architecture.md)。

## API Reference

除 `/health` 外需 Bearer 示範權杖。Task：task_id、title、description、status、created_at、updated_at。

| Method | Endpoint | 功能／成功碼 |
|---|---|---|
| GET | /health | 存活檢查 200 |
| POST | /tasks | 建立 201 |
| GET | /tasks?limit=50&cursor=UUID | 分頁清單 200 |
| GET | /tasks/{id} | 單一任務 200 |
| PATCH | /tasks/{id} | 更新 200 |
| DELETE | /tasks/{id} | 刪除 204 |
| GET | /weather?city=Taipei | 天氣 200 |

[詳細 API、驗證與錯誤格式](docs/api-documentation.md)。

## Local Development Setup

需 Python 3.12；本地 DynamoDB 可選 Docker DynamoDB Local 或無 Docker 的 Moto。從根目錄先建立 venv、安裝 requirements-dev，再於不同 terminal 啟動資料庫、API 與 frontend。[完整可複製指令](docs/deployment.md#本機python-312)。`python -m scripts.init_local_db` 僅接受本地 endpoint，`python -m scripts.dev_server` 只綁定 loopback。靜態前端用 `python -m http.server 8080 --bind 127.0.0.1 --directory frontend`，開啟 http://localhost:8080。兩者需要相同權杖設定。

## Test Instructions

```bash
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest --cov=src --cov-report=term-missing
sam validate --lint --region ap-northeast-1
sam build
```

完整依賴鎖定於 `requirements-lock.txt`（由乾淨 venv 產生），CI 使用此檔安裝；可用 `pip install -r requirements-lock.txt` 重現。pytest 不需真實 AWS 憑證，測試環境只使用 testing credentials，涵蓋 CRUD、輸入、資料庫異常、天氣異常、認證及 CORS。整合測試自動啟動 Moto HTTP :18000 與本地 API :8001，驗證 HTTP CRUD 和獨立 SDK 讀回。先停掉手動 API，勿平行執行。這些證據**不能代替真實 AWS 的 IAM／Gateway 驗收**。[測試輸出](docs/evidence/pytest.txt)、[驗收總表](docs/acceptance-report.md)。

## AWS Deployment Guide

[部署、更新、刪除、認證、預算與監控](docs/deployment.md)。需已授權 AWS profile；`sam validate` → `sam build` → `sam deploy --guided`，填入 AllowedOrigin / DemoToken。由 Outputs.ApiEndpoint 呼叫 API 並執行 `python -m scripts.smoke_test "$API_URL"`。測試結束 `sam delete --stack-name cathay-cloud-demo`，會刪除 Demo table 資料，先確認沒有需保留內容。

## CI/CD Workflow

![CI/CD workflow](docs/cicd.png)

CI：push/PR → Python → dependencies → Ruff → pytest → SAM validate/build → 測試 artifact。CD：main push/manual → verify → opt-in flag/environment → 既有 AWS OIDC role → SAM build/deploy → smoke test。CD 預設不執行，需管理者設定 role、secret、vars。沒有提交 AWS access keys。**本次 GitHub Actions 尚未實際運行**，本地命令成功不等於遠端 CI 成功。

## Git Collaboration Workflow

![GitHub Flow](docs/git-workflow.png)

`main → feature → PR → CI → review → merge → deploy`；採 Conventional Commits、main protection 與 revert rollback。此為**單人專案的多人協作流程設計**，沒有捏造團隊紀錄。[分支、審查、衝突與發布步驟](docs/git-workflow.md)。

## Security Considerations

示範 API 除 health 外需至少 32 字元共用 token，未設定拒絕存取；CORS 僅允許一個來源，HTTPS 為雲端 Gateway 提供。Lambda role 限指定 table 與 log group；輸入大小限制、unknown fields 拒絕、安全錯誤訊息、日誌不含 token／payload，`.gitignore` 排除憑證與設定。

NoEcho 只防止 CloudFormation 常見顯示，Lambda 環境仍可被有權管理者讀取；正式版改 Secrets Manager。共用 token 不具個別撤銷／資料隔離，不可放真實客戶資料。使用者需自己審查後才能公開。未設計企業身份驗證，下一階段採 Cognito / Gateway JWT Authorizer、每使用者分區與逐物件授權。CORS 不是認證，低額預算提醒不是硬性限額。

## AI-assisted Development

AI 實際協助需求拆解、程式、測試、文件與本地 reviewer 檢查。精確模型版本未核實，沒有宣稱人工已審查或虛構多人 review。[真實開發報告](docs/ai-development-report.md)。

## Known Limitations

- 無 AWS credentials，未實際部署、未做雲端 smoke／DynamoDB persistence 證據。
- GitHub CLI 未登入，連接帳號 cfla999-tech 與指定 EricYang938 不符；未遠端寫入／建立 repo／執行 CI。
- 天氣實際連線逾時，僅 mock 路徑與錯誤處理已驗證；需於可連外環境重測。
- 前端本地提供；瀏覽器驗收因環境禁止 Chromium 建立 socket 而 BLOCKED，尚無操作截圖；Docker DynamoDB Local 路徑尚未實測；Moto 重啟不保留資料。
- Scan 無全域排序；共享 token、無登入／個別授權；沒有 SNS 通知、備份、完整 tracing。

## Future Improvements

Cognito/JWT、owner 授權、Query/GSI 與排序、Secrets Manager、資料保留與備份、前端 S3/CloudFront 或既有 HTTPS hosting、預算通知／安全監控。只在需求成立時引入額外服務。

## Assessment Requirements Mapping

| 測驗要求 | 交付位置 | 狀態 |
|---|---|---|
| Python 程式 | src/、tests/ | 本地測試通過 |
| 雲端架構／圖 | template.yaml、docs/architecture.png | 設計／validate／build 通過，未部署 |
| 情境／功能／選型理由 | 本 README、docs/architecture.md | 已撰寫 |
| 原始碼 Repo 或 ZIP | 完整 ZIP（含本地 Git 歷史） | 可交 ZIP，遠端受帳號限制 |
| 前端 | frontend/ | 實際驗收見 acceptance report |
| RESTful API | src/services/weather.py | mock 通過，真實連線受限 |
| CI/CD | .github/workflows/、docs/cicd.png | 已配置，遠端未運行 |
| 多人 Git 流程 | docs/git-workflow.* | 單人模擬設計，無實際多人協作 |
| IaC | template.yaml | validate/build 通過，未部署 |
| AI 說明 | docs/ai-development-report.md | 真實紀錄，待作者人工確認 |

[驗收總表](docs/acceptance-report.md) 記錄逐項證據與限制。[提交郵件草稿](docs/submission-email.md) 只供使用者檢查後自行寄出。

目標 Repository（**不是已完成交付的遠端連結**）：https://github.com/EricYang938/cathay-cloud-backend-assessment
