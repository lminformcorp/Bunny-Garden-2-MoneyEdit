# 兔兔秘密花園 2 金錢修改器 (Bunny Garden 2 Money Trainer)

這是一個專為《兔兔秘密花園 2》開發的開源金錢修改工具。採用 Python 編寫，具備圖形化介面（GUI），並針對 Unity 引擎的記憶體特性進行了深度優化。

## 🌟 功能特色
- **手動選取執行檔**：直接選取遊戲 `.exe`，程式自動對照並連接進程。
- **深層模糊搜尋**：針對金錢最後一碼可能加密或縮放的問題，提供自動截斷搜尋機制。
- **鎖定金額**：防止遊戲中消費導致金額變動。
- **安全掃描**：使用底層 Windows API 遍歷記憶體，避開常見的 Python 庫版本不相容問題。

## 🛠️ 安裝環境
在使用此工具之前，請確保你的電腦已安裝 [Python 3.8+](https://www.python.org/)。

1. **克隆專案**：
   bash
   git clone [https://github.com/lminformcorp/Bunny-Garden-2-MoneyEdit](https://github.com/lminformcorp/Bunny-Garden-2-MoneyEdit)
   cd Bunny-Garden-2-MoneyEdit
   
   
2. 安裝必要套件：
	Bash
	pip install -r requirements.txt

🚀 使用方法

以管理員權限執行 程式（修改記憶體需要此權限）。

Bash
python money.py
點擊 「選取檔案」，找到遊戲的安裝路徑並選擇 BUNNY GARDEN 2.exe。

回到遊戲中，確認目前的金額（例如：168007）。

在修改器中輸入完整金額，點擊 「開始搜尋」。

搜尋成功後，輸入目標金額並點擊 「執行修改」。

⚠️ 注意事項
僅供教育與研究用途：本工具僅用於學習記憶體存取原理。請支持正版遊戲。

防毒軟體誤報：由於本程式會存取其他進程的記憶體，部分防毒軟體可能會彈出警告，請自行評估。

存檔備份：修改前建議先備份遊戲存檔。