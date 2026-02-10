// EmberBurn — Tag Generator Logic
// Handles: create, edit, delete, import/export, templates, live polling

const TagGenerator = (function () {
    'use strict';

    let allTags = [];
    let searchFilter = '';
    let pollTimer = null;
    let pendingImport = null;

    // ── Tag Templates ──
    const TEMPLATES = [
        {
            name: '3-Phase Motor',
            description: 'Standard tags for a 3-phase AC motor',
            tags: [
                { suffix: '.Speed', type: 'float', units: 'RPM', initial_value: 0.0, simulate: true, simulation_type: 'sine', min: 0, max: 1800 },
                { suffix: '.Current.L1', type: 'float', units: 'A', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 0, max: 15 },
                { suffix: '.Current.L2', type: 'float', units: 'A', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 0, max: 15 },
                { suffix: '.Current.L3', type: 'float', units: 'A', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 0, max: 15 },
                { suffix: '.Voltage', type: 'float', units: 'V', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 380, max: 420 },
                { suffix: '.Temperature', type: 'float', units: '°C', initial_value: 20.0, simulate: true, simulation_type: 'random', min: 20, max: 85 },
                { suffix: '.Running', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.Fault', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.Runtime', type: 'int', units: 'hours', initial_value: 0, simulate: true, simulation_type: 'increment', min: 0, max: 100000 }
            ]
        },
        {
            name: 'Tank Level System',
            description: 'Tags for a tank with level, temperature, and valve control',
            tags: [
                { suffix: '.Level', type: 'float', units: '%', initial_value: 50.0, simulate: true, simulation_type: 'sine', min: 0, max: 100 },
                { suffix: '.Temperature', type: 'float', units: '°C', initial_value: 20.0, simulate: true, simulation_type: 'random', min: 15, max: 35 },
                { suffix: '.Pressure', type: 'float', units: 'bar', initial_value: 1.0, simulate: true, simulation_type: 'random', min: 0.5, max: 3 },
                { suffix: '.InletValve', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.OutletValve', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.HighAlarm', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.LowAlarm', type: 'bool', units: '', initial_value: false, simulate: false }
            ]
        },
        {
            name: 'Conveyor System',
            description: 'Tags for a conveyor belt system with encoder and motor',
            tags: [
                { suffix: '.Speed', type: 'float', units: 'm/min', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 0, max: 30 },
                { suffix: '.EncoderCount', type: 'int', units: 'pulses', initial_value: 0, simulate: true, simulation_type: 'increment', min: 0, max: 1000000 },
                { suffix: '.MotorCurrent', type: 'float', units: 'A', initial_value: 0.0, simulate: true, simulation_type: 'random', min: 0, max: 10 },
                { suffix: '.Running', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.E_Stop', type: 'bool', units: '', initial_value: false, simulate: false },
                { suffix: '.ItemCount', type: 'int', units: 'items', initial_value: 0, simulate: true, simulation_type: 'increment', min: 0, max: 999999 }
            ]
        }
    ];

    // ── Initialization ──
    function init() {
        refreshTags();
        startPolling();

        var searchInput = document.getElementById('tag-gen-search');
        if (searchInput) {
            searchInput.addEventListener('input', function (e) {
                searchFilter = e.target.value.toLowerCase();
                renderTable();
            });
        }
    }

    // ── Polling ──
    function startPolling() {
        pollTimer = setInterval(refreshTags, 3000);
    }

    function stopPolling() {
        if (pollTimer) clearInterval(pollTimer);
    }

    async function refreshTags() {
        try {
            var data = await api.getTags();
            if (data && data.tags) {
                allTags = Object.entries(data.tags).map(function (entry) {
                    return {
                        name: entry[0],
                        value: entry[1].value !== undefined ? entry[1].value : entry[1],
                        type: entry[1].type || typeof entry[1].value || 'unknown',
                        quality: entry[1].quality || 'Good',
                        units: entry[1].units || '',
                        description: entry[1].description || ''
                    };
                });
            } else if (data && typeof data === 'object') {
                allTags = Object.entries(data).map(function (entry) {
                    var val = entry[1];
                    if (typeof val === 'object' && val !== null) {
                        return {
                            name: entry[0],
                            value: val.value !== undefined ? val.value : JSON.stringify(val),
                            type: val.type || 'unknown',
                            quality: val.quality || 'Good',
                            units: val.units || '',
                            description: val.description || ''
                        };
                    }
                    return { name: entry[0], value: val, type: typeof val, quality: 'Good', units: '', description: '' };
                });
            }
            updateStatCards();
            renderTable();
        } catch (err) {
            console.error('Tag refresh failed:', err);
        }
    }

    // ── Stat Cards ──
    function updateStatCards() {
        var countEl = document.getElementById('total-tags-count');
        if (countEl) countEl.textContent = allTags.length;
    }

    // ── Table Rendering ──
    function renderTable() {
        var tbody = document.getElementById('tag-gen-table');
        if (!tbody) return;

        var filtered = allTags;
        if (searchFilter) {
            filtered = allTags.filter(function (t) {
                return t.name.toLowerCase().indexOf(searchFilter) !== -1;
            });
        }

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">' +
                (searchFilter ? 'No tags match "' + escapeHtml(searchFilter) + '"' : 'No tags found. Click "+ New Tag" to create one.') +
                '</td></tr>';
            return;
        }

        tbody.innerHTML = filtered.map(function (tag) {
            var qualityClass = 'quality-good';
            if (tag.quality === 'Stale' || tag.quality === 'Uncertain') qualityClass = 'quality-stale';
            if (tag.quality === 'Bad') qualityClass = 'quality-bad';

            return '<tr>' +
                '<td><strong>' + escapeHtml(tag.name) + '</strong></td>' +
                '<td>' + escapeHtml(String(tag.type)) + '</td>' +
                '<td>' + escapeHtml(formatValue(tag.value)) + '</td>' +
                '<td><span class="' + qualityClass + '">● ' + escapeHtml(tag.quality) + '</span></td>' +
                '<td>' + escapeHtml(tag.units) + '</td>' +
                '<td class="tag-actions">' +
                '<button class="btn btn-secondary" onclick="TagGenerator.showWriteModal(\'' + escapeHtml(tag.name) + '\')" title="Write Value">📝</button>' +
                '<button class="btn btn-danger" onclick="TagGenerator.deleteTag(\'' + escapeHtml(tag.name) + '\')" title="Delete">🗑️</button>' +
                '</td>' +
                '</tr>';
        }).join('');
    }

    function formatValue(val) {
        if (val === null || val === undefined) return '--';
        if (typeof val === 'number') return Number.isInteger(val) ? String(val) : val.toFixed(2);
        return String(val);
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Create Tag ──
    function showCreateModal() {
        document.getElementById('create-tag-modal').style.display = 'flex';
    }

    function hideCreateModal() {
        document.getElementById('create-tag-modal').style.display = 'none';
        document.getElementById('create-tag-form').reset();
    }

    async function handleCreateTag(event) {
        event.preventDefault();
        var form = event.target;
        var fd = new FormData(form);

        var tagData = {
            name: fd.get('name'),
            type: fd.get('type'),
            initial_value: fd.get('initial_value'),
            description: fd.get('description') || '',
            units: fd.get('units') || '',
            category: fd.get('category') || '',
            simulate: fd.get('simulate') === 'true',
            simulation_type: fd.get('simulation_type') || 'static',
            min: fd.get('min') ? parseFloat(fd.get('min')) : 0,
            max: fd.get('max') ? parseFloat(fd.get('max')) : 100,
            access: fd.get('access') || 'readwrite'
        };

        // Convert initial_value to correct type
        if (tagData.type === 'float') tagData.initial_value = parseFloat(tagData.initial_value) || 0.0;
        else if (tagData.type === 'int') tagData.initial_value = parseInt(tagData.initial_value, 10) || 0;
        else if (tagData.type === 'bool') tagData.initial_value = tagData.initial_value === 'true';

        try {
            await api.createTag(tagData);
            hideCreateModal();
            refreshTags();
        } catch (err) {
            alert('Failed to create tag: ' + err.message);
        }
    }

    // ── Delete Tag ──
    async function deleteTag(name) {
        if (!confirm('Delete tag "' + name + '"? This cannot be undone.')) return;
        try {
            await api.deleteTag(name);
            refreshTags();
        } catch (err) {
            alert('Failed to delete tag: ' + err.message);
        }
    }

    // ── Write Value ──
    var writeTargetTag = '';

    function showWriteModal(name) {
        writeTargetTag = name;
        document.getElementById('write-tag-name').textContent = name;
        document.getElementById('write-value-input').value = '';
        document.getElementById('write-value-modal').style.display = 'flex';
    }

    function hideWriteModal() {
        document.getElementById('write-value-modal').style.display = 'none';
        writeTargetTag = '';
    }

    async function confirmWriteValue() {
        var value = document.getElementById('write-value-input').value;
        if (!writeTargetTag || value === '') return;
        try {
            await api.writeTag(writeTargetTag, value);
            hideWriteModal();
            refreshTags();
        } catch (err) {
            alert('Failed to write value: ' + err.message);
        }
    }

    // ── Export ──
    async function exportTags(format) {
        try {
            var response = await fetch('/api/tags/export?format=' + format);
            if (!response.ok) throw new Error('Export failed');
            var blob = await response.blob();
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'tags_export.' + format;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            // Fallback: export from client-side data
            var data;
            if (format === 'json') {
                data = JSON.stringify(allTags, null, 2);
                downloadBlob(data, 'tags_export.json', 'application/json');
            } else {
                var csv = 'Name,Type,Value,Units,Description\n';
                allTags.forEach(function (t) {
                    csv += [t.name, t.type, t.value, t.units, t.description].map(function (v) {
                        return '"' + String(v).replace(/"/g, '""') + '"';
                    }).join(',') + '\n';
                });
                downloadBlob(csv, 'tags_export.csv', 'text/csv');
            }
        }
    }

    function downloadBlob(content, filename, mimeType) {
        var blob = new Blob([content], { type: mimeType });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    // ── Import ──
    function showImportModal() {
        document.getElementById('import-modal').style.display = 'flex';
        document.getElementById('import-file').value = '';
        document.getElementById('import-preview').style.display = 'none';
        document.getElementById('confirm-import-btn').disabled = true;
        pendingImport = null;

        document.getElementById('import-file').addEventListener('change', handleFileSelect);
    }

    function hideImportModal() {
        document.getElementById('import-modal').style.display = 'none';
        pendingImport = null;
    }

    function handleFileSelect(event) {
        var file = event.target.files[0];
        if (!file) return;

        var reader = new FileReader();
        reader.onload = function (e) {
            var content = e.target.result;
            try {
                if (file.name.endsWith('.json')) {
                    pendingImport = JSON.parse(content);
                    if (!Array.isArray(pendingImport)) pendingImport = [pendingImport];
                } else {
                    pendingImport = parseCSV(content);
                }
                renderImportPreview(pendingImport);
                document.getElementById('confirm-import-btn').disabled = false;
            } catch (err) {
                alert('Failed to parse file: ' + err.message);
            }
        };
        reader.readAsText(file);
    }

    function parseCSV(text) {
        var lines = text.trim().split('\n');
        if (lines.length < 2) return [];
        var headers = lines[0].split(',').map(function (h) { return h.trim().replace(/^"|"$/g, ''); });
        var tags = [];
        for (var i = 1; i < lines.length; i++) {
            var vals = lines[i].split(',').map(function (v) { return v.trim().replace(/^"|"$/g, ''); });
            var tag = {};
            headers.forEach(function (h, idx) {
                tag[h.toLowerCase().replace(/ /g, '_')] = vals[idx] || '';
            });
            tags.push(tag);
        }
        return tags;
    }

    function renderImportPreview(tags) {
        var preview = document.getElementById('import-preview');
        preview.style.display = 'block';

        var headEl = document.getElementById('import-preview-head');
        var bodyEl = document.getElementById('import-preview-body');

        if (tags.length === 0) {
            headEl.innerHTML = '';
            bodyEl.innerHTML = '<tr><td class="loading">No tags found in file</td></tr>';
            return;
        }

        var keys = Object.keys(tags[0]);
        headEl.innerHTML = '<tr>' + keys.map(function (k) { return '<th>' + escapeHtml(k) + '</th>'; }).join('') + '</tr>';
        bodyEl.innerHTML = tags.slice(0, 20).map(function (t) {
            return '<tr>' + keys.map(function (k) { return '<td>' + escapeHtml(String(t[k] || '')) + '</td>'; }).join('') + '</tr>';
        }).join('');

        if (tags.length > 20) {
            bodyEl.innerHTML += '<tr><td colspan="' + keys.length + '" class="loading">...and ' + (tags.length - 20) + ' more</td></tr>';
        }
    }

    async function confirmImport() {
        if (!pendingImport || pendingImport.length === 0) return;
        try {
            await api.bulkCreateTags(pendingImport);
            hideImportModal();
            refreshTags();
        } catch (err) {
            alert('Import failed: ' + err.message);
        }
    }

    // ── Templates ──
    function showTemplateModal() {
        var list = document.getElementById('template-list');
        list.innerHTML = TEMPLATES.map(function (tmpl, idx) {
            return '<div class="template-item" onclick="TagGenerator.applyTemplate(' + idx + ')">' +
                '<h3>' + escapeHtml(tmpl.name) + '</h3>' +
                '<p>' + escapeHtml(tmpl.description) + '</p>' +
                '<div class="tag-count">' + tmpl.tags.length + ' tags</div>' +
                '</div>';
        }).join('');
        document.getElementById('template-modal').style.display = 'flex';
    }

    function hideTemplateModal() {
        document.getElementById('template-modal').style.display = 'none';
    }

    async function applyTemplate(idx) {
        var tmpl = TEMPLATES[idx];
        if (!tmpl) return;
        var prefix = prompt('Enter a prefix for the tags (e.g. "Line1.Motor1"):', tmpl.name.replace(/ /g, ''));
        if (prefix === null) return;

        var tags = tmpl.tags.map(function (t) {
            return {
                name: prefix + t.suffix,
                type: t.type,
                initial_value: t.initial_value,
                units: t.units,
                simulate: t.simulate !== false,
                simulation_type: t.simulation_type || 'static',
                min: t.min || 0,
                max: t.max || 100,
                description: tmpl.name + ' — ' + t.suffix.replace(/^\./, '')
            };
        });

        try {
            await api.bulkCreateTags(tags);
            hideTemplateModal();
            refreshTags();
        } catch (err) {
            alert('Template apply failed: ' + err.message);
        }
    }

    // ── Public API ──
    return {
        init: init,
        showCreateModal: showCreateModal,
        hideCreateModal: hideCreateModal,
        handleCreateTag: handleCreateTag,
        deleteTag: deleteTag,
        showWriteModal: showWriteModal,
        hideWriteModal: hideWriteModal,
        confirmWriteValue: confirmWriteValue,
        exportTags: exportTags,
        showImportModal: showImportModal,
        hideImportModal: hideImportModal,
        confirmImport: confirmImport,
        showTemplateModal: showTemplateModal,
        hideTemplateModal: hideTemplateModal,
        applyTemplate: applyTemplate
    };
})();

// Auto-init
document.addEventListener('DOMContentLoaded', TagGenerator.init);
