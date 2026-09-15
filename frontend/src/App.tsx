import { useEffect, useState } from 'react';
import { Music, RefreshCw, Trash2, HardDrive, Disc } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8749';

// 曲データの型定義
interface Song {
  filename: string;
  title: string;
  artist: string;
}

function App() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 曲一覧を取得する関数
  const fetchSongs = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/songs/`);
      if (response.ok) {
        const data = await response.json();
        setSongs(data);
      } else {
        console.error('取得エラー:', response.statusText);
      }
    } catch (error) {
      console.error('通信エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 曲を削除する関数
  const handleDelete = async (filename: string) => {
    if (!window.confirm(`「${filename}」をゴミ箱に移動しますか？`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/songs/${filename}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        // 削除成功したらリストを再読み込みして画面を更新
        fetchSongs();
      } else {
        alert('削除に失敗しました。');
      }
    } catch (error) {
      console.error('通信エラー:', error);
      alert('サーバーと通信できませんでした。');
    }
  };

  // 画面が表示された時に1回だけ一覧を取得する
  useEffect(() => {
    fetchSongs();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 p-4 md:p-8 flex justify-center font-sans">
      <div className="max-w-4xl w-full flex flex-col gap-6">
        
        {/* ヘッダー部分 */}
        <div className="flex flex-row items-center justify-between">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-sm">
              <Music className="text-blue-500" size={24} />
            </div>
            YouTube Audio Manager
          </h1>
          <button 
            onClick={fetchSongs}
            className="p-3 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-md transition-colors flex items-center justify-center shrink-0 border border-zinc-800 shadow-sm"
            title="ライブラリを更新"
          >
            <RefreshCw size={18} className={isLoading ? 'animate-spin text-blue-500' : ''} />
          </button>
        </div>

        {/* 曲一覧エリア */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/50 flex justify-between items-center">
            <h2 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
              <HardDrive size={16} />
              ライブラリ ({songs.length}曲)
            </h2>
          </div>

          <div className="divide-y divide-zinc-800/80">
            {isLoading ? (
              <div className="p-12 text-center text-zinc-500 flex flex-col items-center gap-4">
                <RefreshCw size={24} className="animate-spin text-zinc-600" />
                <p>読み込み中...</p>
              </div>
            ) : songs.length === 0 ? (
              <div className="p-12 text-center text-zinc-500 flex flex-col items-center gap-4">
                <Disc size={32} className="text-zinc-700" />
                <p>曲がありません。</p>
              </div>
            ) : (
              songs.map((song) => (
                <div key={song.filename} className="p-4 md:p-6 flex flex-row items-center justify-between hover:bg-zinc-800/50 transition-colors group">
                  
                  {/* アートワーク風のアイコン（仮） */}
                  <div className="w-12 h-12 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/50 shrink-0 mr-4">
                    <Music size={20} className="text-zinc-600" />
                  </div>

                  <div className="flex-1 min-w-0 pr-4 flex flex-col gap-1">
                    <p className="text-base font-medium text-zinc-100 truncate">{song.title}</p>
                    <p className="text-sm text-zinc-400 truncate">{song.artist}</p>
                    <p className="text-xs text-zinc-600 truncate font-mono mt-1">{song.filename}</p>
                  </div>

                  <button
                    onClick={() => handleDelete(song.filename)}
                    className="ml-2 flex-shrink-0 p-3 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-md transition-colors opacity-100 md:opacity-0 md:group-hover:opacity-100 focus:opacity-100"
                    title="削除"
                  >
                    <Trash2 size={20} />
                  </button>
                  
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;