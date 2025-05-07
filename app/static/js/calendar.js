document.addEventListener('DOMContentLoaded', function() {
    // カレンダーの初期化
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        eventSources: [
            {
                url: '/api/calendar/fit2go',
                color: '#0275d8',
                id: 'fit2go'
            },
            {
                url: '/api/calendar/googlefit',
                color: '#5cb85c',
                id: 'googlefit'
            },
            {
                url: '/api/calendar/healthconnect',
                color: '#f0ad4e',
                id: 'healthconnect'
            }
        ],
        eventClick: function(info) {
            showSessionDetails(info.event);
        },
        dateClick: function(info) {
            showDailySummary(info.date);
        }
    });
    calendar.render();

    // データソースの表示/非表示の切り替え
    document.getElementById('showFit2GoData').addEventListener('change', function(e) {
        toggleEventSource('fit2go', e.target.checked);
    });

    document.getElementById('showGoogleFitData').addEventListener('change', function(e) {
        toggleEventSource('googlefit', e.target.checked);
    });

    document.getElementById('showHealthConnectData').addEventListener('change', function(e) {
        toggleEventSource('healthconnect', e.target.checked);
    });

    function toggleEventSource(sourceId, show) {
        const eventSource = calendar.getEventSourceById(sourceId);
        if (show) {
            eventSource.enable();
        } else {
            eventSource.disable();
        }
        calendar.refetchEvents();
    }

    // セッション詳細の表示
    async function showSessionDetails(event) {
        const modal = new bootstrap.Modal(document.getElementById('sessionModal'));
        
        // セッションデータの取得
        const sessionData = await fetchSessionData(event.id);
        const healthData = await fetchIntegratedHealthData(event.start);
        
        // プロット作成
        createSessionPlots(sessionData);
        createHealthMetricsPlot(healthData);
        
        // メトリクス表示
        updateSessionMetrics(sessionData);
        
        modal.show();
    }

    // 日次サマリーの表示
    async function showDailySummary(date) {
        document.getElementById('selected-date').textContent = date.toLocaleDateString();
        
        // 各データソースからデータを取得
        const [fit2goData, googleFitData, healthConnectData] = await Promise.all([
            fetchDailyFit2GoData(date),
            fetchGoogleFitData(date),
            fetchHealthConnectData(date)
        ]);
        
        // データの統合と表示
        const integratedData = integrateHealthData(fit2goData, googleFitData, healthConnectData);
        updateIntegratedStats(integratedData);
        createDailyActivityPlot(integratedData);
    }

    // 統合データの表示更新
    function updateIntegratedStats(data) {
        const integratedStats = document.getElementById('integrated-stats');
        integratedStats.style.display = 'block';
        
        document.getElementById('avg-heart-rate').textContent = 
            data.avgHeartRate ? `${Math.round(data.avgHeartRate)} bpm` : '-- bpm';
        document.getElementById('total-active-time').textContent = 
            data.totalActiveTime ? `${Math.round(data.totalActiveTime)} min` : '-- min';
        document.getElementById('total-calories').textContent = 
            data.totalCalories ? `${Math.round(data.totalCalories)} kcal` : '-- kcal';
        document.getElementById('total-steps').textContent = 
            data.totalSteps ? `${data.totalSteps.toLocaleString()} steps` : '-- steps';
    }

    // データ取得関数
    async function fetchSessionData(sessionId) {
        const response = await fetch(`/api/sessions/${sessionId}`);
        return response.json();
    }

    async function fetchIntegratedHealthData(date) {
        const response = await fetch(`/api/health/integrated/${formatDate(date)}`);
        return response.json();
    }

    async function fetchDailyFit2GoData(date) {
        const response = await fetch(`/api/daily/fit2go/${formatDate(date)}`);
        return response.json();
    }

    async function fetchGoogleFitData(date) {
        const response = await fetch(`/api/daily/googlefit/${formatDate(date)}`);
        return response.json();
    }

    async function fetchHealthConnectData(date) {
        const response = await fetch(`/api/daily/healthconnect/${formatDate(date)}`);
        return response.json();
    }

    // ユーティリティ関数
    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    // プロット作成関数
    function createSessionPlots(data) {
        Plotly.newPlot('session-details-plots', [
            {
                x: data.timestamps,
                y: data.speed,
                name: 'Speed (km/h)',
                type: 'scatter'
            },
            {
                x: data.timestamps,
                y: data.heartRate,
                name: 'Heart Rate (bpm)',
                yaxis: 'y2',
                type: 'scatter'
            }
        ], {
            grid: { rows: 1, columns: 1, pattern: 'independent' },
            yaxis: { title: 'Speed (km/h)' },
            yaxis2: { title: 'Heart Rate (bpm)', overlaying: 'y', side: 'right' }
        });
    }

    function createHealthMetricsPlot(data) {
        Plotly.newPlot('health-metrics-plot', [
            {
                x: data.timestamps,
                y: data.heartRate,
                name: 'Heart Rate',
                type: 'scatter'
            },
            {
                x: data.timestamps,
                y: data.steps,
                name: 'Steps',
                yaxis: 'y2',
                type: 'scatter'
            }
        ], {
            grid: { rows: 1, columns: 1, pattern: 'independent' },
            yaxis: { title: 'Heart Rate (bpm)' },
            yaxis2: { title: 'Steps', overlaying: 'y', side: 'right' }
        });
    }

    function createDailyActivityPlot(data) {
        const trace1 = {
            x: data.timeSlots,
            y: data.activityLevel,
            type: 'bar',
            name: 'Activity Level'
        };

        const trace2 = {
            x: data.timeSlots,
            y: data.heartRate,
            type: 'scatter',
            name: 'Heart Rate',
            yaxis: 'y2'
        };

        const layout = {
            title: 'Daily Activity Overview',
            yaxis: { title: 'Activity Level' },
            yaxis2: {
                title: 'Heart Rate (bpm)',
                overlaying: 'y',
                side: 'right'
            }
        };

        Plotly.newPlot('daily-activity-plot', [trace1, trace2], layout);
    }

    // データ統合関数
    function integrateHealthData(fit2goData, googleFitData, healthConnectData) {
        return {
            avgHeartRate: calculateWeightedAverage([
                { value: fit2goData.avgHeartRate, weight: fit2goData.duration },
                { value: googleFitData.avgHeartRate, weight: googleFitData.duration },
                { value: healthConnectData.avgHeartRate, weight: healthConnectData.duration }
            ]),
            totalActiveTime: (fit2goData.activeTime || 0) + 
                           (googleFitData.activeTime || 0) + 
                           (healthConnectData.activeTime || 0),
            totalCalories: (fit2goData.calories || 0) + 
                         (googleFitData.calories || 0) + 
                         (healthConnectData.calories || 0),
            totalSteps: (fit2goData.steps || 0) + 
                      (googleFitData.steps || 0) + 
                      (healthConnectData.steps || 0),
            timeSlots: mergeTimeSlots([fit2goData, googleFitData, healthConnectData]),
            activityLevel: calculateActivityLevels([fit2goData, googleFitData, healthConnectData]),
            heartRate: mergeHeartRateData([fit2goData, googleFitData, healthConnectData])
        };
    }

    // 統計計算関数
    function calculateWeightedAverage(items) {
        const totalWeight = items.reduce((sum, item) => sum + (item.weight || 0), 0);
        if (totalWeight === 0) return null;
        
        const weightedSum = items.reduce((sum, item) => {
            return sum + (item.value || 0) * (item.weight || 0);
        }, 0);
        
        return weightedSum / totalWeight;
    }

    function mergeTimeSlots(dataSources) {
        const allSlots = new Set();
        dataSources.forEach(source => {
            if (source.timeSlots) {
                source.timeSlots.forEach(slot => allSlots.add(slot));
            }
        });
        return Array.from(allSlots).sort();
    }

    function calculateActivityLevels(dataSources) {
        const timeSlots = mergeTimeSlots(dataSources);
        return timeSlots.map(slot => {
            return Math.max(...dataSources.map(source => 
                source.activityLevels ? (source.activityLevels[slot] || 0) : 0
            ));
        });
    }

    function mergeHeartRateData(dataSources) {
        const timeSlots = mergeTimeSlots(dataSources);
        return timeSlots.map(slot => {
            const values = dataSources
                .map(source => source.heartRates ? source.heartRates[slot] : null)
                .filter(value => value !== null);
            return values.length > 0 ? Math.max(...values) : null;
        });
    }
});