# Evidence index

本次基準：遠端 main 2c8427924d2bec343d985aec3f7333dd586ce638。本次功能受測 commit：eb642eaa672b6007a4012411e5b62a6b0c6ed0bb。

| 檔案 | 來源與範圍 |
|---|---|
| github-baseline-ci.json | 原始 main 的真實 CI，舊 deploy job 為 skipped |
| github-revision-ci.json | PR #1 run 42480510741，job／step 與 artifact digest |
| frontend.json | 該次 CI 原始 artifact，真實 Chromium／HTTP／Moto，不是 AWS |
| ../screenshots/desktop.png、mobile.png | 該次 CI 原始截圖，權杖欄已清空 |
| weather-live-ci.json | 該次 CI 原始真實 Open-Meteo 回應，PASS |
| local-demo.txt | 新啟動器實際啟動、CRUD 與清理結果 |
| pytest.txt、test-results.xml | 本次本地 61 項測試；遠端也通過 |
| lint.txt、sam-validate.txt、sam-build.txt、audit.json | 對應本地檢查結果 |
| environment.txt、frontend-run.txt、weather-live.txt、weather-live.json | 歷史／本地網路限制紀錄，不代表後續 CI 仍被阻擋 |
| clean-install.txt、install.txt、pip-check.txt、packaging.txt、built-handler.txt | 第一輪乾淨環境與本地來源驗證，保留其實際範圍 |

所有 AWS 部署相關結果本次均未執行。Actions artifacts 有到期時間，故已保存主要 JSON 與截圖。後續若修改功能，需重跑該版本 CI；此紀錄不自動代表任意未來 commit 成功。
