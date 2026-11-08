# GitHub Flow

![Git workflow](git-workflow.png)

本專案為單人委託 AI 的作品，不捏造其他開發者或獨立人工審查。本次修正使用真實 feature branch 與 PR；是否經人工 review／合併以 GitHub 紀錄為準。

1. main 保持可建置；分支如 `feature/task-api`、`fix/assessment-no-aws`、`docs/api-guide`。
2. Conventional Commits，例如 `fix: clear stale tasks after failed reconnect`。
3. PR 寫明問題、結果、驗證與限制，使用 `.github/pull_request_template.md`。
4. CI 的 quality 與 frontend 通過後才考慮合併；weather-live 的綠燈僅表示有記錄結果，必須查看 artifact 內的 PASS/BLOCKED。
5. 建議 main protection、禁止 force push、至少一位人工 reviewer；這些是建議，沒有宣稱帳號設定已啟用。
6. 衝突時先更新 feature 分支、逐檔處理、重跑測試，不盲目採 ours/theirs。
7. 回滾用 `git revert <commit>` 建新 PR；資料相容性另行處理，不將程式回滾當作資料回復。

CI 在 main、feature push 與 PR 執行；本次沒有 AWS 部署 workflow，合併不會建立雲端資源。面試官若無 private Repo 權限，應安排讀取權或另外提供 ZIP。
