// グローバル変数
let currentSession = null;
let historyChart = null;
let dailyChart = null;

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
            axis: { range: [0, 40] },
            bar: { color: '#1f77b4' },
            steps: [
                { range: [0, 10], color: 'lightgray' },
                { range: [10, 20], color: '#d3e6f9' },
                { range: [20, 30], color: '#9ecae1' },
                { range: [30, 40], color: '#6baed6' }
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
            axis: { range: [0, 120] },
            bar: { color: '#2ca02c' },
            steps: [
                { range: [0, 30], color: 'lightgray' },
                { range: [30, 60], color: '#d3edd3' },
                { range: [60, 90], color: '#a1d99b' },
                { range: [90, 120], color: '#74c476' }
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

// リアルタイムデータの更新
function updateRealTimeData() {
    fetch('/api/sessions/current')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'no_active_session') {
                resetDisplays();
                return;
            }

            // メーターの更新
            Plotly.update('speed-gauge', {'value': [data.current_speed_kmh]});
            Plotly.update('rpm-gauge', {'value': [data.current_rpm]});
            Plotly.update('mets-gauge', {'value': [data.current_mets]});

            // メトリクスの更新
            document.getElementById('current-distance').textContent = 
                `${data.total_distance_km.toFixed(2)} km`;
            document.getElementById('current-calories').textContent = 
                `${Math.round(data.total_calories_kcal)} kcal`;
            document.getElementById('current-time').textContent = 
                formatTime(data.total_time_seconds);

            // セッション履歴の更新
            updateSessionHistory();
        })
        .catch(error => console.error('Error fetching current session:', error));
}

// セッション履歴の更新
function updateSessionHistory() {
    const endTime = new Date();
    const startTime = new Date(endTime - 30 * 60000); // 過去30分

    fetch(`/api/sessions/history?start=${startTime.toISOFormat()}&end=${endTime.toISOFormat()}`)
        .then(response => response.json())
        .then(data => {
            const traces = [{
                x: data.map(d => d.timestamp),
                y: data.map(d => d.speed_kmh),
                name: 'Speed',
                type: 'scatter'
            }, {
                x: data.map(d => d.timestamp),
                y: data.map(d => d.rpm),
                name: 'RPM',
                type: 'scatter',
                yaxis: 'y2'
            }];

            const layout = {
                title: 'Session History',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Speed (km/h)' },
                yaxis2: {
                    title: 'RPM',
                    overlaying: 'y',
                    side: 'right'
                },
                height: 300,
                margin: { t: 30, r: 50, l: 50, b: 50 }
            };

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