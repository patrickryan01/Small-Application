// EmberBurn API Client
// Handles all API communication with the backend

// Resolve the URL prefix that reaches this pod.
//
// Two deployment modes must both work:
//   1. Direct (ingress / port-forward / NodePort): the page is served at /tags,
//      /config, etc. and the API lives at /api/... on the same origin.
//   2. Embedded in the Embernet Dashboard, which proxies via a query parameter:
//      /api/proxy?target=http://<podIP>:5000/<path>
//
// Mode 2 defeats both absolute and relative paths. An absolute '/api/tags' hits
// the dashboard host directly; a relative 'api/tags' resolves against the
// dashboard's own path (/api/proxy) and yields /api/api/tags. The only correct
// answer is to rebuild the proxy prefix from the current query string.
function emberburnBasePrefix() {
    var match = window.location.search.match(/[?&]target=([^&]*)/);
    if (!match) {
        return '';  // Direct access — same-origin absolute paths are correct.
    }
    var target = decodeURIComponent(match[1]);
    var origin = target.match(/^https?:\/\/[^/]+/);
    if (!origin) {
        return '';  // Malformed target; fall back to same-origin.
    }
    return window.location.pathname + '?target=' + origin[0];
}

// Exposed so page-level scripts build proxy-correct URLs instead of hardcoding
// absolute paths (which silently break only when embedded in the dashboard).
window.emberburnUrl = function (path) {
    return emberburnBasePrefix() + path;
};

const API_BASE = window.emberburnUrl('/api');

// The pod hands the UI its write token via a cookie on HTML responses, so the
// dashboard iframe works with no login. When the deployment sets
// EMBERBURN_UI_WRITES=false no cookie is issued and writes return 401 — the UI
// is read-only by design in that posture.
function emberburnWriteToken() {
    var match = document.cookie.match(/(?:^|;\s*)emberburn_write_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : '';
}

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

class EmberBurnAPI {
    constructor() {
        this.baseURL = API_BASE;
    }

    async fetchJSON(endpoint, options = {}) {
        try {
            const method = (options.method || 'GET').toUpperCase();
            if (MUTATING_METHODS.indexOf(method) !== -1) {
                const token = emberburnWriteToken();
                if (token) {
                    options.headers = Object.assign({}, options.headers, {
                        'X-EmberBurn-Token': token
                    });
                }
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error(
                        'This deployment is read-only from the web UI. ' +
                        'Writes require the X-EmberBurn-Token header.'
                    );
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Tag Methods
    async getTags() {
        return this.fetchJSON('/tags');
    }

    async getTag(tagName) {
        return this.fetchJSON(`/tags/${tagName}`);
    }

    async writeTag(tagName, value) {
        return this.fetchJSON(`/tags/${tagName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value })
        });
    }

    // Publisher Methods
    async getPublishers() {
        return this.fetchJSON('/publishers');
    }

    async togglePublisher(publisherName) {
        return this.fetchJSON(`/publishers/${publisherName}/toggle`, {
            method: 'POST'
        });
    }

    // Alarm Methods
    async getActiveAlarms() {
        return this.fetchJSON('/alarms/active');
    }

    // Health Check
    async healthCheck() {
        return this.fetchJSON('/health');
    }

    // ── Tag Generator CRUD ──

    async createTag(tagData) {
        return this.fetchJSON('/tags/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tagData)
        });
    }

    async deleteTag(tagName) {
        return this.fetchJSON(`/tags/${tagName}`, {
            method: 'DELETE'
        });
    }

    async updateTag(tagName, data) {
        return this.fetchJSON(`/tags/${tagName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }

    async bulkCreateTags(tags) {
        return this.fetchJSON('/tags/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags: tags })
        });
    }

    async exportTags(format) {
        return this.fetchJSON(`/tags/export?format=${format || 'json'}`);
    }

    // NOTE: there is deliberately no importTags() here. Import is parsed
    // client-side in tag_generator.js (JSON and CSV) and submitted through
    // bulkCreateTags() -> POST /api/tags/bulk. A previous importTags() posted to
    // /api/tags/import, which has never existed server-side and always 404'd.
}

// Create global API instance
window.api = new EmberBurnAPI();
