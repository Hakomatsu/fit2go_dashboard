// グローバル変数
let currentSession = null;
let historyChart = null;
let dailyChart = null;
let activeSessionId = null;

// ゲージチャートの設定
const gaugeLayout = {
    width: 300,
    height: 200,
    margin: { t: 60, r: 25, l: 25, b: 25 }
};

// メーターの初期化
function initializeGauges() {
    // スピードメーター
    Plotly.newPlot('speed-gauge', [{
        type: 'indicator',
        mode: 'gauge+number',
        value: 0,
        title: { text: 'Speed (km/h)' },
        gauge: {
            axis: { range: [0, 60] },  // 最大値を60に変更
            bar: { color: '#1f77b4' },
            steps: [
                { range: [0, 15], color: 'lightgray' },
                { range: [15, 30], color: '#d3e6f9' },
                { range: [30, 45], color: '#9ecae1' },
                { range: [45, 60], color: '#6baed6' }
            ]
        }
    }], gaugeLayout);

    // RPMメーター
    Plotly.newPlot('rpm-gauge', [{
        type: 'indicator',
        mode: 'gauge+number',
        value: 0,
        title: { text: 'RPM' },
        gauge: {
            axis: { range: [0, 200] },  // 最大値を200に変更
            bar: { color: '#2ca02c' },
            steps: [
                { range: [0, 50], color: 'lightgray' },
                { range: [50, 100], color: '#d3edd3' },
                { range: [100, 150], color: '#a1d99b' },
                { range: [150, 200], color: '#74c476' }
            ]
        }
    }], gaugeLayout);

    // METsメーター
    Plotly.newPlot('mets-gauge', [{
        type: 'indicator',
        mode: 'gauge+number',
        value: 0,
        title: { text: 'METs' },
        gauge: {
            axis: { range: [0, 10] },
            bar: { color: '#ff7f0e' },
            steps: [
                { range: [0, 3], color: 'lightgray' },
                { range: [3, 5], color: '#fed8b1' },
                { range: [5, 7], color: '#fdae6b' },
                { range: [7, 10], color: '#fd8d3c' }
            ]
        }
    }], gaugeLayout);
}

// セッション履歴グラフの初期化
function initializeHistoryChart() {
    const layout = {
        title: 'Session History',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Value' },
        height: 300,
        margin: { t: 30, r: 30, l: 50, b: 50 }
    };

    historyChart = Plotly.newPlot('session-history-plot', [], layout);
}

// デイリーサマリーグラフの初期化
function initializeDailySummaryChart() {
    const layout = {
        title: 'Daily Activity',
        barmode: 'group',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Value' },
        height: 400,
        margin: { t: 30, r: 30, l: 50, b: 50 }
    };

    dailyChart = Plotly.newPlot('daily-summary-plot', [], layout);
}

// 時間のフォーマット
function formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// 累積時間のフォーマット
function formatTotalTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
}

// セッションの終了
async function endSession(sessionId, autoSync = true) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/end?auto_sync=${autoSync}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            // セッション終了の成功を通知
            showNotification('セッションを終了しました', 'success');
            
            if (result.sync_result) {
                // 同期結果の通知
                if (result.sync_result.google_fit.success) {
                    showNotification('Google Fitと同期しました', 'success');
                }
                if (result.sync_result.health_connect.success) {
                    showNotification('Health Connectと同期しました', 'success');
                }
            }
            
            // アクティブセッションをリセット
            activeSessionId = null;
            resetDisplays();
        } else {
            showNotification('セッションの終了に失敗しました: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error ending session:', error);
        showNotification('セッションの終了中にエラーが発生しました', 'error');
    }
}

// 手動同期
async function syncSession(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.google_fit.success || result.health_connect.success) {
            if (result.google_fit.success) {
                showNotification('Google Fitと同期しました', 'success');
            }
            if (result.health_connect.success) {
                showNotification('Health Connectと同期しました', 'success');
            }
        } else {
            const errors = [];
            if (result.google_fit.error) errors.push(`Google Fit: ${result.google_fit.error}`);
            if (result.health_connect.error) errors.push(`Health Connect: ${result.health_connect.error}`);
            showNotification('同期に失敗しました: ' + errors.join(', '), 'error');
        }
    } catch (error) {
        console.error('Error syncing session:', error);
        showNotification('同期中にエラーが発生しました', 'error');
    }
}

// 通知表示
function showNotification(message, type = 'info') {
    // Bootstrapのトースト通知を使用
    const toastHtml = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
            <div class="toast-header bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} text-white">
                <strong class="me-auto">Fit2Go</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    document.getElementById('toast-container').appendChild(toastElement.firstChild);
    
    const toast = new bootstrap.Toast(document.getElementById('toast-container').lastChild);
    toast.show();
}

// リアルタイムデータの更新
function updateRealTimeData() {
    fetch('/api/sessions/current')
        .then(response => response.json())
        .then(data => {
            // デバッグ出力を追加
            console.log('Received session data:', data);
            
            if (data.status === 'no_active_session') {
                if (activeSessionId) {
                    // アクティブなセッションが終了された場合
                    endSession(activeSessionId);
                }
                resetDisplays();
                return;
            }

            // セッションIDを保存
            activeSessionId = data.session_id;

            // メーターの更新
            Plotly.update('speed-gauge', {'value': [data.current_speed_kmh]});
            Plotly.update('rpm-gauge', {'value': [data.current_rpm]});
            Plotly.update('mets-gauge', {'value': [data.current_mets]});

            // デバッグ出力を追加
            console.log('Updating metrics:');
            console.log('Distance:', data.session_dist_km);
            console.log('Calories:', data.session_cal_kcal);
            console.log('Time:', data.session_time_s);

            // リアルタイムメトリクスの更新（セッションデータ）
            document.getElementById('current-distance').textContent = 
                `${(data.session_dist_km || 0).toFixed(2)} km`;
            document.getElementById('current-calories').textContent = 
                `${(data.session_cal_kcal || 0).toFixed(1)} kcal`;  // 小数点第一位まで表示
            document.getElementById('current-time').textContent = 
                formatTime(data.session_time_s || 0);

            // セッション履歴の更新
            updateSessionHistory();
        })
        .catch(error => {
            console.error('Error fetching current session:', error);
            console.error('Stack trace:', error.stack);
        });
}

// セッション履歴の更新
function updateSessionHistory() {
    const endTime = new Date();
    const startTime = new Date(endTime - 30 * 60000); // 過去30分

    // ISO 8601形式の文字列を生成
    const formatDate = (date) => date.toISOString();

    fetch(`/api/sessions/history?start=${formatDate(startTime)}&end=${formatDate(endTime)}`)
        .then(response => response.json())
        .then(data => {
            // データが空の場合は更新しない
            if (!data || data.length === 0) return;

            const traces = [{
                x: data.map(d => new Date(d.timestamp)),
                y: data.map(d => d.speed_kmh),
                name: 'Speed',
                type: 'scatter',
                line: { color: '#1f77b4' }
            }, {
                x: data.map(d => new Date(d.timestamp)),
                y: data.map(d => d.rpm),
                name: 'RPM',
                type: 'scatter',
                yaxis: 'y2',
                line: { color: '#2ca02c' }
            }];

            const layout = {
                title: 'Session History',
                xaxis: { 
                    title: 'Time',
                    type: 'date',
                    tickformat: '%H:%M:%S'
                },
                yaxis: { 
                    title: 'Speed (km/h)',
                    titlefont: { color: '#1f77b4' },
                    tickfont: { color: '#1f77b4' }
                },
                yaxis2: {
                    title: 'RPM',
                    titlefont: { color: '#2ca02c' },
                    tickfont: { color: '#2ca02c' },
                    overlaying: 'y',
                    side: 'right'
                },
                height: 300,
                margin: { t: 30, r: 50, l: 50, b: 50 }
            };

            // グラフを更新（データがない場合は更新しない）
            Plotly.react('session-history-plot', traces, layout);
        })
        .catch(error => console.error('Error fetching session history:', error));
}

// デイリーサマリーの更新
function updateDailySummary() {
    fetch('/api/sessions/daily')
        .then(response => response.json())
        .then(data => {
            const traces = [{
                x: data.map(d => d.time),
                y: data.map(d => d.avg_speed),
                name: 'Avg Speed',
                type: 'bar'
            }, {
                x: data.map(d => d.time),
                y: data.map(d => d.avg_rpm),
                name: 'Avg RPM',
                type: 'bar'
            }];

            Plotly.react('daily-summary-plot', traces);
        })
        .catch(error => console.error('Error fetching daily summary:', error));
}

// 累積データの更新
function updateCumulativeStats() {
    fetch('/api/sessions/cumulative')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-time').textContent = 
                formatTotalTime(data.total_time_seconds);
            document.getElementById('total-distance').textContent = 
                `${data.total_distance_km.toFixed(2)} km`;
            document.getElementById('total-calories').textContent = 
                `${Math.round(data.total_calories_kcal)} kcal`;
        })
        .catch(error => console.error('Error fetching cumulative stats:', error));
}

// ディスプレイのリセット
function resetDisplays() {
    Plotly.update('speed-gauge', {'value': [0]});
    Plotly.update('rpm-gauge', {'value': [0]});
    Plotly.update('mets-gauge', {'value': [0]});
    
    document.getElementById('current-distance').textContent = '0.00 km';
    document.getElementById('current-calories').textContent = '0 kcal';
    document.getElementById('current-time').textContent = '00:00:00';
}

// 初期化と定期更新の設定
window.addEventListener('load', () => {
    initializeGauges();
    initializeHistoryChart();
    initializeDailySummaryChart();
    
    // 定期更新の設定
    setInterval(updateRealTimeData, 1000);     // リアルタイムデータ（1秒）
    setInterval(updateDailySummary, 60000);    // デイリーサマリー（1分）
    setInterval(updateCumulativeStats, 60000); // 累積データ（1分）
    
    // 初回データ取得
    updateRealTimeData();
    updateDailySummary();
    updateCumulativeStats();
});