document.addEventListener('DOMContentLoaded', function() {
    let calendar;
    
    initializeCalendar();
    loadSessionDates();
    
    function initializeCalendar() {
        const calendarEl = document.getElementById('calendar');
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'ja',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            dateClick: function(info) {
                loadDailyStats(info.dateStr);
            },
            eventClick: function(info) {
                showSessionDetails(info.event.extendedProps.sessionId);
            }
        });
        
        calendar.render();
    }
    
    function loadSessionDates() {
        fetch('/api/sessions/dates')
            .then(response => response.json())
            .then(data => {
                const events = data.map(session => ({
                    title: 'Workout',
                    start: session.start_time,
                    end: session.end_time,
                    backgroundColor: '#007bff',
                    extendedProps: {
                        sessionId: session.id
                    }
                }));
                
                calendar.removeAllEvents();
                calendar.addEventSource(events);
            })
            .catch(error => console.error('Error loading session dates:', error));
    }
    
    function loadDailyStats(dateStr) {
        fetch(`/api/sessions/daily?date=${dateStr}`)
            .then(response => response.json())
            .then(data => {
                const statsContainer = document.getElementById('daily-stats');
                if (data.length === 0) {
                    statsContainer.innerHTML = '<p class="text-muted">No activity recorded for this date</p>';
                    return;
                }
                
                // 日次サマリーの作成
                const totalDistance = data.reduce((sum, d) => sum + d.total_distance, 0);
                const totalCalories = data.reduce((sum, d) => sum + d.total_calories, 0);
                const sessionCount = new Set(data.map(d => d.session_id)).size;
                
                statsContainer.innerHTML = `
                    <div class="daily-stat">
                        <h6>Total Sessions</h6>
                        <p>${sessionCount}</p>
                    </div>
                    <div class="daily-stat">
                        <h6>Total Distance</h6>
                        <p>${totalDistance.toFixed(2)} km</p>
                    </div>
                    <div class="daily-stat">
                        <h6>Total Calories</h6>
                        <p>${Math.round(totalCalories)} kcal</p>
                    </div>
                `;
                
                // アクティビティグラフの作成
                const traces = [{
                    x: data.map(d => d.time),
                    y: data.map(d => d.avg_speed),
                    name: 'Average Speed',
                    type: 'bar'
                }, {
                    x: data.map(d => d.time),
                    y: data.map(d => d.avg_rpm),
                    name: 'Average RPM',
                    type: 'bar'
                }];
                
                const layout = {
                    title: 'Daily Activity',
                    barmode: 'group',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Value' },
                    height: 300,
                    margin: { t: 30, r: 30, l: 50, b: 50 }
                };
                
                Plotly.newPlot('daily-activity-plot', traces, layout);
            })
            .catch(error => console.error('Error loading daily stats:', error));
    }
    
    function showSessionDetails(sessionId) {
        fetch(`/api/sessions/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                const modalEl = document.getElementById('sessionModal');
                const modal = new bootstrap.Modal(modalEl);
                
                // セッション詳細のプロット作成
                const timeData = data.data_points.map(d => d.timestamp);
                const plotData = [{
                    x: timeData,
                    y: data.data_points.map(d => d.speed_kmh),
                    name: 'Speed',
                    type: 'scatter'
                }, {
                    x: timeData,
                    y: data.data_points.map(d => d.rpm),
                    name: 'RPM',
                    type: 'scatter',
                    yaxis: 'y2'
                }];
                
                const layout = {
                    title: 'Session Details',
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
                
                Plotly.newPlot('session-details-plots', plotData, layout);
                
                // セッションメトリクスの表示
                document.getElementById('session-metrics').innerHTML = `
                    <div class="row">
                        <div class="col-md-4">
                            <div class="metric-card">
                                <h6>Total Time</h6>
                                <p>${formatTime(data.total_time_seconds)}</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <h6>Total Distance</h6>
                                <p>${data.total_distance_km.toFixed(2)} km</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <h6>Total Calories</h6>
                                <p>${Math.round(data.total_calories_kcal)} kcal</p>
                            </div>
                        </div>
                    </div>
                `;
                
                modal.show();
            })
            .catch(error => console.error('Error loading session details:', error));
    }
    
    function formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }
});