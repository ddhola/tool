from flask import Flask, render_template, request, Response
import subprocess
import os

app = Flask(__name__)

# 設定預設下載路徑
DOWNLOAD_PATH = r"D:\Python\Downloads"
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>YouTube 批量下載器 - 徹底去 NA 版</title>
        <style>
            body { font-family: "Microsoft JhengHei", sans-serif; padding: 40px; background-color: #f8f9fa; }
            .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h2 { color: #333; border-left: 5px solid #ff0000; padding-left: 15px; margin-bottom: 20px; }
            textarea { width: 100%; height: 200px; padding: 15px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-family: monospace; font-size: 14px; }
            .terminal { background-color: #1e1e1e; color: #d4d4d4; padding: 15px; height: 350px; overflow-y: scroll; border-radius: 8px; font-family: monospace; font-size: 13px; line-height: 1.5; white-space: pre-wrap; }
            .controls { display: flex; gap: 10px; margin-bottom: 20px; }
            button { background-color: #ff0000; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: bold; flex-grow: 1; font-size: 16px; }
            button:hover { background-color: #cc0000; }
            select { padding: 10px; border-radius: 8px; border: 1px solid #ddd; font-size: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🚀 YouTube 下載進度監控</h2>
            <form id="downloadForm">
                <textarea name="urls" id="urls" placeholder="在此貼上多行網址..."></textarea>
                <div class="controls">
                    <select name="format" id="format">
                        <option value="mp3">🎧 下載 MP3 (320K)</option>
                        <option value="mp4">🎬 下載 MP4 (1080p)</option>
                    </select>
                    <button type="button" onclick="startDownload()">開始下載並顯示進度</button>
                </div>
            </form>
            <div class="terminal" id="progress">等待任務啟動...</div>
        </div>

        <script>
            function startDownload() {
                const terminal = document.getElementById('progress');
                const urls = document.getElementById('urls').value;
                const format = document.getElementById('format').value;

                if (!urls.trim()) return alert("請先貼上網址！");

                terminal.innerHTML = "正在啟動下載引擎...\\n";

                fetch('/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `urls=${encodeURIComponent(urls)}&format=${format}`
                }).then(response => {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    function read() {
                        reader.read().then(({done, value}) => {
                            if (done) {
                                terminal.innerHTML += "\\n✅ 所有任務執行完畢！";
                                return;
                            }
                            terminal.innerHTML += decoder.decode(value);
                            terminal.scrollTop = terminal.scrollHeight; 
                            read();
                        });
                    }
                    read();
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/download', methods=['POST'])
def download():
    urls_raw = request.form.get('urls')
    fmt = request.form.get('format')

    # 分割網址
    url_list = [u.strip() for u in urls_raw.replace(' ', '\n').split('\n') if u.strip()]

    def generate():
        for i, url in enumerate(url_list):
            yield f"\n[任務 {i + 1}/{len(url_list)}] 正在處理: {url}\n"

            # --- 分開處理命名邏輯 ---
            # 如果網址包含 "list=" 代表是清單，我們使用編號
            if "list=" in url:
                # 清單模式：[編號]. [標題].[副檔名]
                output_tmpl = os.path.join(DOWNLOAD_PATH, "%(playlist_index)s. %(title)s.%(ext)s")
                cmd = ["yt-dlp", "--newline", "--output", output_tmpl]
            else:
                # 單影片模式：[標題].[副檔名] (完全不使用 playlist 變數，徹底避開 NA)
                output_tmpl = os.path.join(DOWNLOAD_PATH, "%(title)s.%(ext)s")
                cmd = ["yt-dlp", "--newline", "--no-playlist", "--output", output_tmpl]

            # 格式設定
            if fmt == "mp3":
                cmd += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "320K", "--embed-thumbnail", "--add-metadata"]
            else:
                cmd += ["-f", "bestvideo[height<=1080]+bestaudio[ext=m4a]", "-S", "vcodec:h264", "--merge-output-format", "mp4", "--embed-thumbnail", "--add-metadata"]

            cmd.append(url)

            # 執行並讀取進度
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            for line in process.stdout:
                # 這裡過濾掉含有 NA 的行（選做，增加視覺乾淨度）
                yield line
            process.wait()

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=5000)