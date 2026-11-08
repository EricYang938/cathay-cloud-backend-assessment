# 實作重新驗收報告

日期：2026-11-08（Asia/Taipei）。基準：遠端 main `2c8427924d2bec343d985aec3f7333dd586ce638`，與本地基準 commit 相同。依使用者最早貼出的原始題目與完整任務書核對；使用者後續明確決定不部署 AWS，此決定取代任務書中的實際部署目標。

**本次交付範圍：可執行 Python、雲端架構設計／圖、情境與選型說明、Git Repository、單元／本地 HTTP 整合、CI、前端及外部 API 程式。AWS 仍是設計方案，不是已部署系統。** 無法保證官方未提供的評分標準，亦不把後來擴充任務書的工程目標當作原始題目明文規定。

## 真實遠端證據

- Repository 已存在且以 EricYang938 授權讀寫；目前 private，面試官需取得存取權或另收 ZIP。
- [原始版本 CI 成功](https://github.com/EricYang938/cathay-cloud-backend-assessment/actions/runs/42474750413)：quality 的 dependency install、Ruff、pytest、SAM validate/build、artifact 全部成功。
- [舊 opt-in workflow](https://github.com/EricYang938/cathay-cloud-backend-assessment/actions/runs/42474750388)：verify 成功，但 **deploy job skipped**，不是 AWS 成功。本次移除該 workflow，沒有 AWS credentials／deploy 步驟。
- [本次修正的真實 CI 成功](https://github.com/EricYang938/cathay-cloud-backend-assessment/actions/runs/42480510741)，受測 commit：`eb642eaa672b6007a4012411e5b62a6b0c6ed0bb`。quality、frontend、weather-live 全部成功；已額外核實 weather step 本身成功且 JSON.status=PASS，不只看 workflow 綠燈。
- [修正 PR #1](https://github.com/EricYang938/cathay-cloud-backend-assessment/pull/1) 提供實際 feature → PR → CI 紀錄；未宣稱其他人已 review 或合併。
- CI runner：Python 3.12、Chromium；前端真實本地 HTTP／Moto 操作通過，Open-Meteo 真實 HTTPS 回應通過。這不涉及 AWS 部署。

## Requirement Matrix

| Requirement | Type | Status | Evidence | Issue |
|---|---|---|---|---|
| Python 原始碼可執行 | Mandatory | PASS | src/、tests/、docs/evidence/pytest.txt | 本地與遠端 quality 證據 |
| 情境與功能說明 | Mandatory | PASS | README、api-documentation.md | 與實作對照 |
| 雲端架構圖 | Mandatory | PASS | architecture.png / svg / dot | 清楚標示未部署及 AWS 邊界 |
| AWS 服務選型理由 | Mandatory | PASS | README 選型表、architecture.md | Lambda/EC2、DynamoDB/RDS、成本與維運取捨 |
| Git Repo 或 ZIP | Mandatory | PASS | 本 Repository、本地 Git 歷史 | private，需作者提供面試官讀取權或 ZIP |
| 前端 CRUD／錯誤／loading／響應式 | Bonus | PASS | evidence/frontend.json、screenshots/desktop.png、screenshots/mobile.png | CI Chromium CRUD、獨立 HTTP 狀態讀回、錯誤及 390px 無橫向溢位通過 |
| 第三方 RESTful API | Bonus | PASS | evidence/weather-live-ci.json、weather-evidence artifact | 2026-11-08 20:29（台灣）真實 Taipei 查詢成功；本地逾時歷史另存 |
| CI 與流程圖 | Bonus | PASS | .github/workflows/ci.yml、cicd.png、evidence/github-revision-ci.json | 新版 quality／frontend／weather-live 實際結果已核對 |
| AWS CD | Bonus | NOT IMPLEMENTED | 無 deploy workflow | 依使用者決定排除，本次不做 |
| 多人 Git 工作流程設計 | Bonus | PASS | git-workflow.*、PR template | 單人示範，沒有捏造多人 review |
| SAM IaC | Bonus | PASS | template.yaml、sam-validate.txt、sam-build.txt | validate/build，不等於雲端可用證明 |
| AI 使用說明 | Bonus | PASS | ai-development-report.md | AI 自審不是獨立人工審查 |
| 單元與本地 HTTP 整合測試 | Engineering Enhancement | PASS | pytest.txt、test-results.xml | HTTP→handler→boto3→Moto，不是 AWS |
| 獨立資料庫用戶端讀回 | Engineering Enhancement | PASS | test_separate_client_reads_persisted_item | 僅本地 Moto |
| 新版一鍵本地 Demo | Engineering Enhancement | PASS | scripts/run_local.py、evidence/local-demo.txt | 啟動三個服務、HTTP CRUD、清除 token 已實測 |
| 認證、CORS、驗證與安全錯誤 | Engineering Enhancement | PASS | 單元測試、src/app.py | 共用 token，無個人帳號隔離 |
| 全新環境相依安裝 | Engineering Enhancement | PASS | requirements-lock.txt、clean-install.txt、真實 CI | 沒有假設使用者已有 Python 3.12 |
| 本地圖片／連結與常見金鑰掃描 | Engineering Enhancement | PASS | scripts.audit_project、audit.json | 只掃常見格式，不是全面安全保證 |
| 真實 AWS 部署、IAM、CloudWatch 與雲端持久化 | Engineering Enhancement | NOT TESTED | template.yaml／未來參考手冊 | 依使用者決定不執行，不列為本次未完成必做項 |
| Docker DynamoDB Local | Engineering Enhancement | NOT TESTED | compose.yaml | 本次使用 Moto，Docker 非必要 |
| 人工獨立 review／main protection | Engineering Enhancement | NOT TESTED | git-workflow.md 建議 | 未宣稱已由其他人審查或啟用設定 |
| 提交郵件 | Engineering Enhancement | PASS | submission-email.md | 草稿，未寄出 |

## 命令與驗收界線

| 命令／流程 | 預期結果 | 證據位置 |
|---|---|---|
| `pytest --cov=src --cov-report=term-missing` | 所有測試成功 | docs/evidence/pytest.txt |
| `ruff check .`、`ruff format --check .` | 無 lint／格式錯誤 | docs/evidence/lint.txt |
| `sam validate --lint`、`sam build` | 有效範本、建置成功 | sam-validate.txt、sam-build.txt |
| `python -m scripts.run_local` + smoke | 不使用 AWS 的 Demo 可操作 | local-demo.txt（實際執行後才建立） |
| `python -m scripts.verify_frontend` | Chromium CRUD、獨立 HTTP 狀態讀回、錯誤、390px 無溢位 | CI frontend-evidence artifact／frontend.json |
| `python -m scripts.verify_weather` | 真實供應者成功或明確 BLOCKED | CI weather-evidence artifact／weather-live.json |
| `python -m scripts.audit_project` | 本地連結與常見秘密格式無錯誤 | audit.json |

weather-live job 使用 continue-on-error，避免公共服務暫時不可用阻擋核心 CRUD；**workflow 綠燈不代表天氣 live 通過**。必須讀取該次 weather-evidence 中的 status。UI 使用 mock 的天氣回應也不會列作真實外部 API 證據。

## 已完成補驗與證據

- `pytest`：61 passed；src coverage 98%。`ruff`、依賴完整性、JS syntax、offline audit、SAM validate/build 均成功。
- 本地啟動器：已用不存在的繼承 AWS_PROFILE 實測，能隔離 AWS 身分、啟動 Moto／API／前端、完成 CRUD，Ctrl+C 後刪除 token，console 不列印權杖。
- 前端：[桌機截圖](screenshots/desktop.png)、[手機截圖](screenshots/mobile.png)、[自動化檢查](evidence/frontend.json)。圖中權杖欄已清空，資料為測試建立的示範任務。
- 天氣：[CI 原始成功 JSON](evidence/weather-live-ci.json)，真實 Open-Meteo geocoding 與 current 回應；不是 fixture。原本本地網路逾時仍保留於 weather-live.json / weather-live.txt。
- CI provenance：[job、step、artifact ID 與 SHA256](evidence/github-revision-ci.json)。下載的 screenshots／JSON 為該 run 的原始 artifact，沒有重製成假成功。

## 剩餘界線

本次不要求開 AWS 帳號，也不補雲端部署。提交前作者應確認私人 Repo 存取權、人工閱讀程式與架構說明，並把最新 Actions URL／artifacts 提供面試官。舊 evidence 的失敗紀錄屬歷史，不刪掉或改成假成功；新版證據以時間戳與 CI commit 為準。
