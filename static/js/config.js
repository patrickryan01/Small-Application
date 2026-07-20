// Config View Logic
// Backs the Server Information panel and the Quick Actions on the Config page.
// These actions used to be alert('Feature coming soon!') stubs.

var ConfigPage = (function () {

    // ── Server information ──

    async function loadServerInfo() {
        try {
            // The API index reports its own endpoints, including the GraphQL
            // URL built from the requesting host rather than "localhost".
            var response = await fetch(window.emberburnUrl('/api'));
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var info = await response.json();

            setText('info-rest-api', window.location.origin + '/api/');
            setText('info-graphql', (info.endpoints && info.endpoints.graphql) || 'Not enabled');
            setText('info-version', 'EmberBurn v' + (info.version || 'unknown'));
        } catch (error) {
            console.error('Server info error:', error);
            setText('info-rest-api', 'Unavailable');
            setText('info-graphql', 'Unavailable');
        }
    }

    function setText(id, value) {
        var el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    // ── Export config ──

    async function exportConfig() {
        try {
            var response = await fetch(window.emberburnUrl('/api/config'));
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var config = await response.json();

            var blob = new Blob([JSON.stringify(config, null, 2)],
                { type: 'application/json' });
            var url = URL.createObjectURL(blob);
            var link = document.createElement('a');
            link.href = url;
            link.download = 'emberburn-config.json';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Config export error:', error);
            alert('Could not export config: ' + error.message);
        }
    }

    // ── Log viewer ──

    async function viewLogs() {
        var modal = document.getElementById('logs-modal');
        var output = document.getElementById('logs-output');
        modal.style.display = 'flex';
        output.textContent = 'Loading…';

        try {
            var response = await fetch(window.emberburnUrl('/api/logs?limit=200'));
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var data = await response.json();

            if (!data.logs || data.logs.length === 0) {
                output.textContent = 'No log records buffered yet.';
                return;
            }

            output.textContent = data.logs.map(function (entry) {
                var stamp = new Date(entry.timestamp * 1000).toISOString();
                return stamp + '  ' + entry.level.padEnd(8) + entry.logger + '  ' + entry.message;
            }).join('\n');

            // Show the newest lines first-visible.
            output.scrollTop = output.scrollHeight;
        } catch (error) {
            console.error('Log fetch error:', error);
            output.textContent = 'Could not load logs: ' + error.message;
        }
    }

    function hideLogs() {
        document.getElementById('logs-modal').style.display = 'none';
    }

    document.addEventListener('DOMContentLoaded', loadServerInfo);

    return {
        exportConfig: exportConfig,
        viewLogs: viewLogs,
        hideLogs: hideLogs
    };
})();
