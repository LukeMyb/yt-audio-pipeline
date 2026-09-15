import { useEffect, useState } from 'react';

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
    <div className="min-h-screen bg-gray-50 p-8 flex justify-center">
      <div className="max-w-3xl w-full">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">YouTube Audio Manager</h1>

        {/* 曲一覧エリア */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-100 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-700">ライブラリ ({songs.length}曲)</h2>
            <button 
              onClick={fetchSongs}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              更新
            </button>
          </div>

          <div className="divide-y divide-gray-200">
            {isLoading ? (
              <div className="p-6 text-center text-gray-500">読み込み中...</div>
            ) : songs.length === 0 ? (
              <div className="p-6 text-center text-gray-500">曲がありません。</div>
            ) : (
              songs.map((song) => (
                <div key={song.filename} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex-1 min-w-0 pr-4">
                    <p className="text-lg font-medium text-gray-900 truncate">{song.title}</p>
                    <p className="text-sm text-gray-500 truncate">{song.artist}</p>
                    <p className="text-xs text-gray-400 mt-1 truncate font-mono">{song.filename}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(song.filename)}
                    className="ml-4 flex-shrink-0 bg-red-100 text-red-600 px-4 py-2 rounded font-medium hover:bg-red-200 transition-colors"
                  >
                    削除
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