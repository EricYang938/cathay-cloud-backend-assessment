# 實作驗收報告

驗收日期：2026-11-08（Asia/Taipei）。依使用者提供的任務書逐項核對；未取得完整官方題目原件，因此「符合要求」判斷限於該任務書列出的要求。執行方式與完整結果見下方證據。

**結論：可交付原始碼 ZIP、Python 後端、架構圖、選型說明與本地驗證證據；尚不能宣稱已完成 AWS 部署、GitHub CI 或六項加分全部驗收。** 原始必要交付的程式／文件／圖／ZIP 已具備；若官方另要求公開 Git URL 或實際雲端網址，仍需補驗。這不是以程式碼生成替代驗收。

## Requirement Matrix

| Requirement | Type | Status | Evidence | Issue |
|---|---|---|---|---|
| Python 原始碼可執行 | Mandatory | PASS | src/；[pytest](evidence/pytest.txt) | Python 3.12 全新 venv 執行 |
| 應用情境說明完整 | Mandatory | PASS | [README](../README.md) | 示範任務管理，不用真實金融資料 |
| 主要功能說明 | Mandatory | PASS | [API 文件](api-documentation.md)、src/ | 端點與回應對照實作 |
| 雲端架構圖完整且可閱讀 | Mandatory | PASS | [PNG](architecture.png)、[設計說明](architecture.md) | 明確標示未部署與 AWS／外部邊界 |
| AWS 選型理由完整 | Mandatory | PASS | README 選型表、architecture.md | 含 Lambda/EC2、DynamoDB/RDS 與成本取捨 |
| Git Repository 或 ZIP | Mandatory | PASS | 完整 ZIP，包含本地 .git 歷史 | GitHub 遠端受帳號限制；ZIP 解壓／clone 驗證另見 packaging 證據 |
| 前端程式與實際操作 | Bonus | BLOCKED | frontend/、[瀏覽器啟動紀錄](evidence/frontend-run.txt) | JS 語法檢查通過；Chromium socket 被環境拒絕，未驗證互動／響應式，無操作截圖 |
| 第三方 RESTful API 真實整合 | Bonus | BLOCKED | src/services/weather.py、[live 結果](evidence/weather-live.txt) | mock 含正常／timeout／HTTP errors；實際網路逾時，不能判 PASS |
| CI/CD 圖與實際配置一致 | Bonus | PASS | [流程圖](cicd.png)、.github/workflows/ | 人工對照檔案；不是遠端執行成功 |
| Git 多人協作工作流程 | Bonus | PASS | [流程文件](git-workflow.md)、[圖](git-workflow.png) | 單人模擬設計，沒有實際多人 review／PR |
| SAM IaC 語法與建置 | Bonus | PASS | [validate](evidence/sam-validate.txt)、[build](evidence/sam-build.txt) | 只驗證 template/build，不代表 cloud runtime |
| AI 使用說明 | Bonus | PASS | [開發報告](ai-development-report.md) | 真實說明 AI 自審；使用者人工審查 NOT TESTED |
| 單元測試 | Engineering Enhancement | PASS | pytest / JUnit XML | CRUD、驗證、錯誤、Auth、CORS、weather mocks |
| HTTP API 整合測試 | Engineering Enhancement | PASS | tests/integration/test_http.py；pytest | 真實 HTTP → handler → boto3 → Moto；非 AWS |
| 資料庫寫入與獨立用戶端讀回 | Engineering Enhancement | PASS | test_separate_client_reads_persisted_item | 只有本地 Moto 證據，雲端讀回 BLOCKED |
| Lint / format / JS syntax | Engineering Enhancement | PASS | [Lint](evidence/lint.txt)、[JS](evidence/js-syntax.txt) | 不等於瀏覽器互動通過 |
| 全新 Python 環境安裝 | Engineering Enhancement | PASS | [clean install](evidence/clean-install.txt)、[pip check](evidence/pip-check.txt) | requirements-lock.txt 記錄實際解出的版本 |
| 常見硬編碼金鑰與私鑰掃描 | Engineering Enhancement | PASS | [offline audit](evidence/audit.json) | 只檢查常見格式，不保證涵蓋所有秘密 |
| 部署文件可重現 | Engineering Enhancement | NOT TESTED | [部署手冊](deployment.md) | 本地路徑已測；AWS guided 步驟未實際部署 |
| Lambda IAM 權限範圍 | Engineering Enhancement | PASS | template.yaml / SAM validate | 靜態審查限定 table/log ARN；雲端實際授權未驗證 |
| 部署 OIDC Role 最小權限 | Engineering Enhancement | NOT IMPLEMENTED | deployment.md 設定指南 | 沒有建立／變更帳號 IAM；需管理者依 ARN 配置 |
| README 本地圖片與相對檔案連結 | Engineering Enhancement | PASS | audit.json | 未驗證所有外部網址當下可用 |
| GitHub Actions 真實成功 run | Engineering Enhancement | BLOCKED | [環境紀錄](evidence/environment.txt) | CLI 未登入，連接帳號與指定帳號不符；沒有 run URL |
| 目標 GitHub Repo clone | Engineering Enhancement | BLOCKED | environment.txt | 遠端 404 可能是不存在或無權限，未捏造遠端完成 |
| AWS 實際部署與 HTTPS smoke test | Engineering Enhancement | BLOCKED | environment.txt | 無 AWS credentials，未建立付費資源 |
| AWS DynamoDB 雲端讀回 | Engineering Enhancement | BLOCKED | deployment.md 補驗步驟 | 不用 Moto 證據替代 |
| Docker DynamoDB Local | Engineering Enhancement | NOT TESTED | compose.yaml | 此環境無 Docker executable |
| CORS、14 天 logs、節流與 monitoring | Engineering Enhancement | PASS | template.yaml、test_auth_and_cors | 靜態範本／本地單元測試；雲端與 alarm 發送 NOT TESTED |
| 企業登入與逐使用者隔離 | Engineering Enhancement | NOT IMPLEMENTED | README security | 本題展示採共用 token，未宣稱企業級 |
| 提交郵件草稿 | Engineering Enhancement | PASS | [草稿](submission-email.md) | 尚未寄出，需填姓名／收件人 |

## Commands / Expected / Actual

| 執行命令 | 預期 | 實際結果 | Status | 證據 |
|---|---|---|---|---|
| `python -m pip install -r requirements-dev.txt`（全新 venv） | 安裝成功 | 成功，依賴衝突修正後重跑 | PASS | evidence/clean-install.txt |
| `python -m pip check`（全新 venv） | 無缺漏／衝突 | No broken requirements found | PASS | evidence/pip-check.txt |
| `ruff check .` | 無錯誤 | All checks passed | PASS | evidence/lint.txt |
| `ruff format --check .` | 格式一致 | all files formatted | PASS | evidence/lint.txt |
| `pytest --cov=src --cov-report=term-missing --junitxml=docs/evidence/test-results.xml` | 所有測試成功 | 61 passed，src 覆蓋率 98% | PASS | evidence/pytest.txt、test-results.xml |
| `sam validate --lint --region ap-northeast-1` | 範本有效 | valid SAM Template | PASS | evidence/sam-validate.txt |
| `sam build` | Lambda 套件建置成功 | Build Succeeded | PASS | evidence/sam-build.txt |
| `node --check frontend/app.js` | JS syntax 正確 | exit 0 | PASS | evidence/js-syntax.txt |
| `python -m scripts.verify_frontend` | 實際瀏覽器 CRUD／響應式 | Chromium 啟動 socket Operation not permitted | BLOCKED | evidence/frontend-run.txt |
| `WeatherService().query('Taipei')` | live API 回傳城市天氣 | provider timed out（受控 504） | BLOCKED | evidence/weather-live.txt |
| `python -m scripts.audit_project` | 本地連結／圖檔與常見秘密檢查無錯誤 | 詳見 JSON | PASS | evidence/audit.json |
| `gh auth status` | EricYang938 可寫入 | CLI 未登入；連接帳號 cfla999-tech | BLOCKED | evidence/environment.txt |
| `sam deploy` | CloudFormation stack 成功 | 未執行，無 AWS credentials | BLOCKED | evidence/environment.txt |
| `python -m scripts.smoke_test <cloud-url>` | 雲端 CRUD 成功 | 尚無 cloud URL，未執行 | NOT TESTED | deployment.md |

單元測試不需要 AWS 帳號。HTTP smoke 流程為 POST → GET → PATCH → GET → DELETE → GET 404；已在本地 Moto 上實際執行。該測試不驗證 API Gateway、IAM、CloudWatch 或真實 AWS 的持久性。

## 補驗順序

1. 使用者以 EricYang938 登入 GitHub 並確認 repo 權限；檢查是否已有內容，避免覆蓋；推送後取得 CI 成功 run URL。
2. 在有已授權 AWS profile 的環境部署 SAM，記錄 Outputs、CloudWatch 與 smoke 結果，獨立讀回 DynamoDB，檢查費用後清理。
3. 在可啟動 Chromium 的環境執行 verify_frontend；保留 desktop/mobile 截圖並確認無水平溢位。
4. 於可連外的環境重試 Open-Meteo，保留來源、時間戳與實際回應；需要時依公司代理設定調整網路。
5. 作者人工審查所有程式與說明，更新報告與郵件，只有有證據的新增成功才改 PASS。

截止依任務書為 **2026-11-09 12:00（台灣時間）**。本報告未將尚未執行的項目標成成功；不宣稱 GitHub URL 或公開網站目前可供面試官使用。
