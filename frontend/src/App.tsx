import { useEffect, useState } from 'react';
import { Music, RefreshCw, Trash2, HardDrive, Disc, Download, Plus, Search, X } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8749';

// 曲データの型定義
interface Song {
  filename: string;
  title: string;
  artist: string;
}

// サムネイルコンポーネント
const Thumbnail = ({ filename }: { filename: string }) => {
  const [hasError, setHasError] = useState(false);
  
  if (hasError) {
    return (
      <div className="w-10 h-10 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/50 shrink-0 mr-3">
        <Music size={18} className="text-zinc-600" />
      </div>
    );
  }
  
  return (
    <img
      src={`${API_BASE_URL}/api/songs/${encodeURIComponent(filename)}/thumbnail`}
      alt="Thumbnail"
      className="w-10 h-10 rounded-md object-cover border border-zinc-700/50 shrink-0 mr-3 bg-zinc-800"
      onError={() => setHasError(true)}
    />
  );
};

function App() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [urlInput, setUrlInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSong, setSelectedSong] = useState<Song | null>(null);

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
        setStatusMessage(`「${filename}」を削除しました`);
        fetchSongs();
      } else {
        setStatusMessage('削除に失敗しました。');
      }
    } catch (error) {
      console.error('通信エラー:', error);
      setStatusMessage('サーバーと通信できませんでした。');
    }
  };

  // 画面が表示された時に1回だけ一覧を取得する
  useEffect(() => {
    fetchSongs();
  }, []);

  // SSEによるリアルタイムステータス受信（ポーリング不要・超低負荷）
  useEffect(() => {
    // サーバーと1本の持続的な通信パイプを繋ぐ
    const eventSource = new EventSource(`${API_BASE_URL}/status/stream`);

    // サーバーから新しいデータが「プッシュ送信」された時だけ発火する
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status) {
          setStatusMessage(data.status);
        }
        
        // 処理が完了したサインを受け取ったらライブラリを更新
        if (!data.is_active && data.status && (data.status.includes('ReplayGainタグを埋め込みました') || data.status.includes('エラーが発生しました'))) {
          fetchSongs();
        }
      } catch (e) {
        console.error("SSE parse error", e);
      }
    };

    // コンポーネントがアンマウントされたら通信を切断する
    return () => {
      eventSource.close();
    };
  }, []);

  // モーダル表示中の背景スクロールロック
  useEffect(() => {
    if (selectedSong) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [selectedSong]);

  // URL送信処理
  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsSubmitting(true);
    setStatusMessage('追加リクエストを送信中...');

    try {
      const response = await fetch(`${API_BASE_URL}/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: urlInput.trim() }),
      });

      if (response.ok) {
        setUrlInput('');
      } else {
        setStatusMessage('エラーが発生しました。');
      }
    } catch (error) {
      console.error('通信エラー:', error);
      setStatusMessage('サーバーと通信できませんでした。');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 検索クエリで曲を絞り込む
  const filteredSongs = songs.filter(song => {
    const q = searchQuery.toLowerCase();
    return song.title.toLowerCase().includes(q) || 
           song.artist.toLowerCase().includes(q) || 
           song.filename.toLowerCase().includes(q);
  });

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 p-4 md:p-8 flex justify-center font-sans">
      <div className="max-w-4xl w-full flex flex-col gap-6">
        
        {/* ステータスメッセージ */}
        <div className="h-6">
          {statusMessage && (
            <p className="text-lg font-medium text-green-400 animate-in fade-in duration-300">{statusMessage}</p>
          )}
        </div>

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

        {/* URL追加フォーム（一時的に無効化） 
        <form onSubmit={handleAddUrl} className="flex gap-2 w-full">
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="YouTubeのURLを入力して追加..."
            className="flex-1 p-3.5 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-600 transition-shadow shadow-sm"
            disabled={isSubmitting}
          />
          <button
            type="submit"
            disabled={!urlInput.trim() || isSubmitting}
            className="px-6 py-3.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-medium rounded-xl transition-colors flex items-center gap-2 shrink-0 shadow-sm"
          >
            {isSubmitting ? (
              <RefreshCw size={18} className="animate-spin" />
            ) : (
              <Plus size={18} />
            )}
            <span className="hidden sm:inline">追加</span>
          </button>
        </form>
        */}

        {/* 検索窓 */}
        <div className="flex flex-row gap-2 w-full">
          <div className="relative grow flex items-center">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="曲名やアーティスト名を入力..."
              className="p-3.5 pr-10 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-600 transition-shadow shadow-sm w-full min-w-0"
            />
            {searchQuery && (
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => setSearchQuery("")}
                className="absolute right-3 p-2 text-zinc-500 hover:text-white rounded-full transition-colors flex items-center justify-center"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* 曲一覧エリア */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/50 flex justify-between items-center">
            <h2 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
              <HardDrive size={16} />
              ライブラリ ({filteredSongs.length}曲)
            </h2>
          </div>

          <div className="divide-y divide-zinc-800/80">
            {isLoading ? (
              <div className="p-12 text-center text-zinc-500 flex flex-col items-center gap-4">
                <RefreshCw size={24} className="animate-spin text-zinc-600" />
                <p>読み込み中...</p>
              </div>
            ) : filteredSongs.length === 0 ? (
              <div className="p-12 text-center text-zinc-500 flex flex-col items-center gap-4">
                {searchQuery ? <Search size={32} className="text-zinc-700" /> : <Disc size={32} className="text-zinc-700" />}
                <p>{searchQuery ? '一致する曲が見つかりません。' : '曲がありません。'}</p>
              </div>
            ) : (
              filteredSongs.map((song) => (
                <div 
                  key={song.filename} 
                  onClick={() => setSelectedSong(song)}
                  className="p-2 md:p-3 flex flex-row items-center justify-between hover:bg-zinc-800/50 transition-colors group cursor-pointer"
                >
                  
                  {/* サムネイル画像（エラー時は自動で音符アイコンにフォールバック） */}
                  <Thumbnail filename={song.filename} />

                  <div className="flex-1 min-w-0 pr-4 flex flex-col justify-center">
                    <p className="text-sm font-medium text-zinc-100 truncate">{song.title}</p>
                    <p className="text-xs text-zinc-400 truncate mt-0.5">{song.artist}</p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(song.filename);
                    }}
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

      {/* 曲の詳細モーダルダイアログ */}
      {selectedSong && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={() => setSelectedSong(null)}
        >
          <div 
            className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden flex flex-col relative animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setSelectedSong(null)}
              className="absolute top-3 right-3 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors z-10 backdrop-blur-md"
            >
              <X size={20} />
            </button>
            
            {/* 大きなサムネイル */}
            <div className="w-full aspect-square bg-zinc-800 relative flex items-center justify-center">
               <img 
                 src={`${API_BASE_URL}/api/songs/${encodeURIComponent(selectedSong.filename)}/thumbnail`} 
                 className="w-full h-full object-cover" 
                 alt="Thumbnail"
                 onError={(e) => {
                   e.currentTarget.style.display = 'none';
                   e.currentTarget.parentElement?.classList.add('bg-zinc-800');
                 }}
               />
               <Music size={64} className="text-zinc-700 absolute -z-10" />
            </div>
            
            <div className="p-5 flex flex-col gap-4">
              <div>
                <h3 className="text-xl font-bold text-white leading-tight">{selectedSong.title}</h3>
                <p className="text-zinc-400 mt-1">{selectedSong.artist}</p>
              </div>
              
              {/* オーディオプレイヤー */}
              <div className="w-full mt-2">
                <audio 
                  controls 
                  autoPlay
                  className="w-full h-10 outline-none" 
                  src={`${API_BASE_URL}/api/songs/${encodeURIComponent(selectedSong.filename)}/download`}
                />
              </div>

              <div className="bg-zinc-950 rounded-xl p-3 border border-zinc-800/80 mt-2">
                <p className="text-[11px] text-zinc-500 mb-1 font-semibold uppercase tracking-wider">File Name</p>
                <p className="text-xs text-zinc-300 font-mono break-all">{selectedSong.filename}</p>
              </div>
              
              <div className="flex gap-2 mt-2">
                <a 
                  href={`${API_BASE_URL}/api/songs/${encodeURIComponent(selectedSong.filename)}/download`}
                  download={selectedSong.filename}
                  className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors flex items-center justify-center gap-2 font-medium"
                >
                  <Download size={18} />
                  ダウンロード
                </a>
                <button
                  onClick={() => {
                    setSelectedSong(null);
                    handleDelete(selectedSong.filename);
                  }}
                  className="p-3 bg-zinc-800 hover:bg-red-500/20 text-zinc-300 hover:text-red-400 rounded-xl transition-colors flex items-center justify-center border border-zinc-700 hover:border-red-500/30"
                  title="削除"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;