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
});
