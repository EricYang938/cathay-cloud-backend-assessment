# AI 輔助開發紀錄

本專案由 OpenAI Codex / ChatGPT Work 的 coding agent 依使用者任務書協助開發；介面未提供可核實的精確模型版本，不猜測。這不是多人協作紀錄。

## 實際用途

AI 讀取需求、撰寫 Python 分層 API、DynamoDB repository、天氣 client、前端、SAM 與 Actions，產生 Graphviz 架構圖、測試及繁中文件，實際執行本地檢查。第一輪曾受 GitHub 帳號與網路環境限制；後續已連接 EricYang938 並讀取真實 Repository 與 CI。使用者明確指定不部署 AWS，因此未建立雲端資源。

## 審查與修正

Agent 以 reviewer 視角檢查資料流、條件式更新與刪除、錯誤遮蔽、權杖 fail closed、CORS、IAM 範圍及文件一致性；**這屬 AI 自審，不是使用者已完成人工審查，也不是獨立人員審核**。交件前作者應逐段閱讀程式與報告，理解測試限制。

實際發現 AWS SAM CLI 釘選 boto3 版本與最初選用版本衝突，依安裝器結果調整 requirements 並重新驗證安裝；Ruff 找到長行與測試過度寬鬆的 Exception assertion，已修正。直接 Open-Meteo 連線實測逾時，保留實際結果，未以 mock 成功宣稱真實串接驗收。

## 人工審查建議與理解重點

作者應能解釋：HTTP event 如何到 Router、驗證、Service、Repository；為什麼 PATCH 用 atomic UpdateItem 而非先讀再整筆覆寫；CloudWatch 的 Lambda Errors 不包含已捕捉並回應的 503；CORS 為何不是認證；Scan 分頁為何只適合少量 Demo；NoEcho 為何不等於 Secrets Manager；本地 Moto 為何不能證明 AWS IAM 與 Gateway 正常。

AI 可快速建立一致的初稿並修正可重現錯誤，但仍可能選錯相依版本、漏掉部署環境限制，不能替代安全審查與實際部署。沒有量測人工基準工時，因此不宣稱「效率提高幾倍」。需求、決策與失敗結果均應由作者確認後承擔最終責任。

## 本次重新驗收與修正

已讀取遠端 main（2c8427924d2bec343d985aec3f7333dd586ce638）與真實 Actions：原有 CI 成功，deploy job 為 skipped。修正文檔過時狀態、移除 AWS deploy workflow、新增無 AWS 的本地啟動器與 CI 瀏覽器／live-weather 證據流程；修正重新連線失敗後殘留可點選舊任務的問題。前端 mock 與真實網路結果分開記錄，僅依後續 CI 的實際結果更新驗收。
