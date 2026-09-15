Set objFSO = CreateObject("Scripting.FileSystemObject")
' VBSファイル自身が置かれているフォルダのパスを自動取得
currentDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
    
' yt-dlpのアップデートを裏で実行
' 仮想環境のpipを使って更新。ネットワークエラー等で失敗しても次に進む
updateCommand = "cmd /c cd /d """ & currentDir & """ && .venv\Scripts\python.exe -m pip install -U yt-dlp"
' 第3引数を True にすることで、アップデートが完了（またはタイムアウト）するまで待機する
' 0は「ウィンドウを非表示にする」、Falseは「実行の完了を待たない（裏で動かし続ける）」
WshShell.Run updateCommand, 0, True

' アップデート完了後、サーバーを起動
startCommand = "cmd /c cd /d """ & currentDir & """ && .venv\Scripts\python.exe -m src.main"
' 第3引数を False にすることで、完了を待たずに裏で動かし続ける
WshShell.Run startCommand, 0, False

' ダッシュボード（フロントエンド）をプレビュー環境で起動
frontendCommand = "cmd /c cd /d """ & currentDir & "\frontend"" && npm run preview"
WshShell.Run frontendCommand, 0, False