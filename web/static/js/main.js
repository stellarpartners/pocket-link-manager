// Main JavaScript file

// Add number formatting helper for Jinja2 templates
if (typeof Number.prototype.toLocaleString === 'undefined') {
    Number.prototype.toLocaleString = function() {
        return this.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };
}

// Initialize tooltips and other interactive elements
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here
    console.log('Pocket Link Manager loaded');
    
    // Initialize Lucide icons if not already done
    if (window.lucide) {
        window.lucide.createIcons();
    }
});

/**
 * Refresh metadata for a link from its live URL
 * @param {number} linkId - The ID of the link to refresh
 * @param {HTMLElement} btn - Optional button element to show loading state
 */
function refreshMetadata(linkId, btn = null) {
    if (!btn) {
        btn = document.getElementById('refresh-metadata-btn-' + linkId) || document.getElementById('refresh-metadata-btn');
    }
    
    if (!btn) return;
    
    const icon = btn.querySelector('i[data-lucide="refresh-cw"]') || btn.querySelector('.refresh-icon') || btn.querySelector('i');
    const originalDisabled = btn.disabled;
    
    btn.disabled = true;
    if (icon) icon.classList.add('spinning');
    
    fetch(`/links/${linkId}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Flash success message if possible or just reload
            window.location.reload();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            btn.disabled = originalDisabled;
            if (icon) icon.classList.remove('spinning');
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
        btn.disabled = originalDisabled;
        if (icon) icon.classList.remove('spinning');
    });
}

/**
 * Convert a link to markdown and sync to Obsidian
 * @param {number} linkId - The ID of the link to convert
 * @param {HTMLElement} btn - Optional button element to show loading state
 */
function convertToMarkdown(linkId, btn = null) {
    // Handle multiple buttons (like top/bottom in detail page)
    const btns = btn ? [btn] : [
        document.getElementById('convert-to-markdown-btn-top'),
        document.getElementById('convert-to-markdown-btn-bottom'),
        document.getElementById('convert-btn-' + linkId)
    ].filter(b => b !== null);
    
    btns.forEach(b => {
        const btnText = b.querySelector('.convert-btn-text');
        const btnSpinner = b.querySelector('.convert-btn-spinner');
        const icon = b.querySelector('i[data-lucide="refresh-cw"]') || b.querySelector('.convert-icon') || b.querySelector('i');
        
        b.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnSpinner) btnSpinner.style.display = 'inline';
        if (icon) icon.classList.add('spinning');
    });
    
    fetch(`/links/${linkId}/convert-to-markdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            btns.forEach(b => {
                const btnText = b.querySelector('.convert-btn-text');
                const btnSpinner = b.querySelector('.convert-btn-spinner');
                const icon = b.querySelector('i[data-lucide="refresh-cw"]') || b.querySelector('.convert-icon') || b.querySelector('i');
                
                b.disabled = false;
                if (btnText) btnText.style.display = 'inline';
                if (btnSpinner) btnSpinner.style.display = 'none';
                if (icon) icon.classList.remove('spinning');
            });
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
        btns.forEach(b => {
            const btnText = b.querySelector('.convert-btn-text');
            const btnSpinner = b.querySelector('.convert-btn-spinner');
            const icon = b.querySelector('i[data-lucide="refresh-cw"]') || b.querySelector('.convert-icon') || b.querySelector('i');
            
            b.disabled = false;
            if (btnText) btnText.style.display = 'inline';
            if (btnSpinner) btnSpinner.style.display = 'none';
            if (icon) icon.classList.remove('spinning');
        });
    });
}
