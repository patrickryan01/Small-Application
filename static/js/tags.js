// Tags View Logic

let tagsUpdater = null;
let currentFilter = 'all';
let currentSearch = '';
let tagMetadata = {};

async function updateTagsView() {
    try {
        // Get tag discovery data with metadata
        const response = await fetch(window.emberburnUrl('/api/tags/discovery'));
        const data = await response.json();
        tagMetadata = {};
        
        // Store metadata
        data.tags.forEach(tag => {
            tagMetadata[tag.name] = tag;
        });
        
        renderTagsTable(data);
        updateFilterCounts(data);
    } catch (error) {
        console.error('Tags update error:', error);
    }
}

function updateFilterCounts(data) {
    const categories = {};
    data.tags.forEach(tag => {
        const cat = tag.category || 'general';
        categories[cat] = (categories[cat] || 0) + 1;
    });
    
    // Update category filter dropdown if it exists
    const filterDropdown = document.getElementById('category-filter');
    if (filterDropdown) {
        filterDropdown.innerHTML = `
            <option value="all">All Categories (${data.tags.length})</option>
            ${Object.entries(categories).map(([cat, count]) => 
                `<option value="${cat}">${cat.charAt(0).toUpperCase() + cat.slice(1)} (${count})</option>`
            ).join('')}
        `;
    }
}

function renderTagsTable(data) {
    const tbody = document.getElementById('tags-table');
    const tags = data.tags || [];

    if (tags.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No tags available</td></tr>';
        return;
    }

    tbody.innerHTML = tags.map(tag => {
        const quality = tag.quality || 'good';
        const qualityBadge = quality === 'good' 
            ? '<span class="badge badge-success">Good</span>'
            : quality === 'bad'
            ? '<span class="badge badge-error">Bad</span>'
            : '<span class="badge badge-warning">Uncertain</span>';
        
        const categoryBadge = `<span class="badge badge-info">${escapeHTML(tag.category || 'general')}</span>`;
        
        const unitsDisplay = tag.units ? ` <span style="color: #888;">${escapeHTML(tag.units)}</span>` : '';
        
        return `
        <tr data-category="${tag.category || 'general'}" data-type="${tag.type}">
            <td style="font-weight: bold;">
                ${escapeHTML(tag.name)}
                ${tag.writable ? ' <span style="color: var(--fire-yellow);" title="Writable">✎</span>' : ''}
            </td>
            <td style="color: var(--fire-yellow); font-size: 18px;">
                ${escapeHTML(String(tag.value))}${unitsDisplay}
            </td>
            <td>${escapeHTML(tag.type)}</td>
            <td title="${escapeHTML(tag.description || '')}">${escapeHTML(truncate(tag.description || 'No description', 40))}</td>
            <td>${categoryBadge}</td>
            <td>${qualityBadge}</td>
            <td>
                <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;" 
                        onclick="showTagDetails('${escapeHTML(tag.name)}')">
                    📊 Details
                </button>
            </td>
        </tr>
        `;
    }).join('');
}

function truncate(str, maxLen) {
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function filterTags(category) {
    currentFilter = category;
    applyFilters();
}

function searchTags(searchTerm) {
    currentSearch = searchTerm.toLowerCase();
    applyFilters();
}

function applyFilters() {
    const rows = document.querySelectorAll('#tags-table tr');
    rows.forEach(row => {
        const rowCategory = row.getAttribute('data-category');
        const tagName = row.querySelector('td:first-child')?.textContent.toLowerCase() || '';
        
        const categoryMatch = currentFilter === 'all' || rowCategory === currentFilter;
        const searchMatch = currentSearch === '' || tagName.includes(currentSearch);
        
        row.style.display = (categoryMatch && searchMatch) ? '' : 'none';
    });
}

async function showTagDetails(tagName) {
    const tag = tagMetadata[tagName];
    if (!tag) {
        alert('Tag metadata not available');
        return;
    }
    
    const details = `
<div style="background: var(--ember-dark); padding: 20px; border-radius: 8px;">
    <h2 style="color: var(--flame-orange); margin-top: 0;">${tag.name}</h2>
    
    <div style="margin: 10px 0;">
        <strong>Current Value:</strong> 
        <span style="color: var(--fire-yellow); font-size: 20px;">${tag.value}</span>
        ${tag.units ? ` ${tag.units}` : ''}
    </div>
    
    <div style="margin: 10px 0;">
        <strong>Description:</strong> ${tag.description || 'No description'}
    </div>
    
    <div style="margin: 10px 0;">
        <strong>Data Type:</strong> ${tag.type}
    </div>
    
    <div style="margin: 10px 0;">
        <strong>Category:</strong> ${tag.category || 'general'}
    </div>
    
    ${tag.min !== null && tag.min !== undefined ? `
    <div style="margin: 10px 0;">
        <strong>Range:</strong> ${tag.min} to ${tag.max} ${tag.units || ''}
    </div>
    ` : ''}
    
    <div style="margin: 10px 0;">
        <strong>Quality:</strong> ${tag.quality || 'good'}
    </div>
    
    <div style="margin: 10px 0;">
        <strong>Writable:</strong> ${tag.writable ? 'Yes' : 'No'}
    </div>
    
    ${tag.simulation_type ? `
    <div style="margin: 10px 0;">
        <strong>Simulation:</strong> ${tag.simulation_type}
    </div>
    ` : ''}
    
    <div style="margin: 10px 0;">
        <strong>Last Update:</strong> ${formatTimestamp(tag.timestamp)}
    </div>
</div>
    `;
    
    // Create modal
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: var(--card-bg);
        padding: 20px;
        border-radius: 8px;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
    `;
    
    content.innerHTML = details + `
        <button class="btn btn-primary" style="margin-top: 20px;" onclick="this.closest('[style*=fixed]').remove()">
            Close
        </button>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Initialize tags view
document.addEventListener('DOMContentLoaded', () => {
    tagsUpdater = new AutoUpdater(updateTagsView, 2000);
    tagsUpdater.start();
    
    // Setup filter and search
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', (e) => filterTags(e.target.value));
    }
    
    const searchInput = document.getElementById('tag-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => searchTags(e.target.value));
    }
});

// Cleanup
window.addEventListener('beforeunload', () => {
    if (tagsUpdater) tagsUpdater.stop();
});
