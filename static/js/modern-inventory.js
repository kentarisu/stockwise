/**
 * Modern Sales & Inventory Management System JavaScript
 * Enhanced with contemporary interaction patterns and animations
 * Based on 2024 UX best practices
 */

class ModernInventorySystem {
    constructor() {
        this.init();
        this.setupAnimations();
        this.setupInteractions();
        this.setupTheme();
        this.setupNotifications();
    }

    init() {
        // Initialize system
        console.log('Modern Inventory System initialized');
        this.setupEventListeners();
        this.preloadAssets();
        this.setupPerformanceOptimizations();
    }

    setupAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.stat-card, .modern-card, .action-btn').forEach(el => {
            observer.observe(el);
        });

        // Stagger animations for grid items
        this.staggerAnimations('.stats-grid .stat-card', 100);
        this.staggerAnimations('.action-buttons .action-btn', 150);
    }

    staggerAnimations(selector, delay) {
        const elements = document.querySelectorAll(selector);
        elements.forEach((el, index) => {
            el.style.animationDelay = `${index * delay}ms`;
        });
    }

    setupInteractions() {
        // Enhanced hover effects
        this.setupHoverEffects();
        
        // Smooth scrolling for internal links
        this.setupSmoothScrolling();
        
        // Enhanced form interactions
        this.setupFormEnhancements();
        
        // Keyboard navigation
        this.setupKeyboardNavigation();
        
        // Touch gestures for mobile
        this.setupTouchGestures();
    }

    setupHoverEffects() {
        // Magnetic effect for buttons
        document.querySelectorAll('.btn-modern, .action-btn').forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                btn.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px) scale(1.02)`;
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translate(0, 0) scale(1)';
            });
        });

        // Parallax effect for cards
        document.querySelectorAll('.stat-card, .modern-card').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;
                
                const rotateX = (y - 0.5) * 10;
                const rotateY = (x - 0.5) * -10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
            });
        });
    }

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupFormEnhancements() {
        // Floating labels
        document.querySelectorAll('.form-control, .form-select').forEach(input => {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-floating-wrapper';
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            
            // Add floating animation
            input.addEventListener('focus', () => {
                wrapper.classList.add('focused');
            });
            
            input.addEventListener('blur', () => {
                if (!input.value) {
                    wrapper.classList.remove('focused');
                }
            });
            
            // Check if already has value
            if (input.value) {
                wrapper.classList.add('focused');
            }
        });

        // Real-time validation
        document.querySelectorAll('input[type="email"], input[type="number"]').forEach(input => {
            input.addEventListener('input', this.validateInput.bind(this));
            input.addEventListener('blur', this.validateInput.bind(this));
        });
    }

    validateInput(e) {
        const input = e.target;
        const value = input.value;
        let isValid = true;
        let message = '';

        // Email validation
        if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            isValid = emailRegex.test(value);
            message = isValid ? '' : 'Please enter a valid email address';
        }

        // Number validation
        if (input.type === 'number' && value) {
            isValid = !isNaN(value) && parseFloat(value) >= 0;
            message = isValid ? '' : 'Please enter a valid positive number';
        }

        // Update UI
        input.classList.toggle('is-valid', isValid && value);
        input.classList.toggle('is-invalid', !isValid && value);

        // Show/hide validation message
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback && message) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.appendChild(feedback);
        }
        if (feedback) {
            feedback.textContent = message;
            feedback.style.display = message ? 'block' : 'none';
        }
    }

    setupKeyboardNavigation() {
        // Enhanced keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('#searchInput');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.show');
                if (activeModal) {
                    const modal = bootstrap.Modal.getInstance(activeModal);
                    if (modal) modal.hide();
                }
            }
        });
    }

    setupTouchGestures() {
        // Swipe gestures for mobile navigation
        let startX, startY, distX, distY;
        const threshold = 150;
        
        document.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const touch = e.changedTouches[0];
            distX = touch.clientX - startX;
            distY = touch.clientY - startY;
            
            // Horizontal swipe
            if (Math.abs(distX) > Math.abs(distY)) {
                if (Math.abs(distX) > threshold) {
                    if (distX > 0) {
                        this.handleSwipeRight();
                    } else {
                        this.handleSwipeLeft();
                    }
                }
            }
            
            startX = startY = null;
        });
    }

    handleSwipeRight() {
        // Open sidebar on mobile
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && window.innerWidth <= 768) {
            sidebar.classList.add('active');
        }
    }

    handleSwipeLeft() {
        // Close sidebar on mobile
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    }

    setupTheme() {
        // Theme switching functionality
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Listen for system theme changes
        prefersDark.addEventListener('change', (e) => {
            this.updateTheme(e.matches ? 'dark' : 'light');
        });
        
        // Initialize theme
        const savedTheme = localStorage.getItem('theme') || 
                          (prefersDark.matches ? 'dark' : 'light');
        this.updateTheme(savedTheme);
    }

    updateTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle button if exists
        const themeToggle = document.querySelector('#themeToggle');
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' ? 
                '<i class="bi bi-sun"></i>' : 
                '<i class="bi bi-moon"></i>';
        }
    }

    setupNotifications() {
        // Enhanced notification system
        this.notificationQueue = [];
        this.createNotificationContainer();
    }

    createNotificationContainer() {
        if (!document.querySelector('#notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} animate-slide-up`;
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icon}</div>
                <div class="notification-message">${message}</div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="bi bi-x"></i>
                </button>
            </div>
            <div class="notification-progress"></div>
        `;
        
        const container = document.querySelector('#notification-container');
        container.appendChild(notification);
        
        // Animate progress bar
        const progress = notification.querySelector('.notification-progress');
        progress.style.animation = `notificationProgress ${duration}ms linear forwards`;
        
        // Auto remove
        setTimeout(() => {
            notification.classList.add('notification-exit');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, duration);
        
        return notification;
    }

    getNotificationIcon(type) {
        const icons = {
            success: '<i class="bi bi-check-circle-fill"></i>',
            error: '<i class="bi bi-exclamation-triangle-fill"></i>',
            warning: '<i class="bi bi-exclamation-circle-fill"></i>',
            info: '<i class="bi bi-info-circle-fill"></i>'
        };
        return icons[type] || icons.info;
    }

    setupEventListeners() {
        // Enhanced search functionality
        const searchInput = document.querySelector('#searchInput');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 300);
            });
        }
        
        // Enhanced filter functionality
        const filterSelect = document.querySelector('#filterSelect');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.applyFilter(e.target.value);
            });
        }
        
        // Refresh functionality
        const refreshBtn = document.querySelector('#refreshTable');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshData();
            });
        }
    }

    performSearch(query) {
        // Enhanced search with highlighting
        const tableRows = document.querySelectorAll('#inventoryTable tbody tr');
        const searchTerm = query.toLowerCase().trim();
        
        tableRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm);
            
            row.style.display = matches || !searchTerm ? '' : 'none';
            
            // Highlight matches
            if (matches && searchTerm) {
                this.highlightText(row, searchTerm);
            } else {
                this.removeHighlight(row);
            }
        });
        
        // Update results count
        const visibleRows = Array.from(tableRows).filter(row => 
            row.style.display !== 'none'
        ).length;
        
        this.updateResultsCount(visibleRows, tableRows.length);
    }

    highlightText(element, searchTerm) {
        // Remove existing highlights
        this.removeHighlight(element);
        
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        textNodes.forEach(textNode => {
            const text = textNode.textContent;
            const regex = new RegExp(`(${searchTerm})`, 'gi');
            
            if (regex.test(text)) {
                const highlightedText = text.replace(regex, '<mark class="search-highlight">$1</mark>');
                const wrapper = document.createElement('span');
                wrapper.innerHTML = highlightedText;
                textNode.parentNode.replaceChild(wrapper, textNode);
            }
        });
    }

    removeHighlight(element) {
        const highlights = element.querySelectorAll('.search-highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }

    updateResultsCount(visible, total) {
        let counter = document.querySelector('.results-counter');
        if (!counter) {
            counter = document.createElement('div');
            counter.className = 'results-counter';
            const tableHeader = document.querySelector('.table-header');
            if (tableHeader) {
                tableHeader.appendChild(counter);
            }
        }
        
        counter.textContent = visible === total ? 
            `${total} items` : 
            `${visible} of ${total} items`;
    }

    applyFilter(filterValue) {
        // Enhanced filtering with animations
        const tableRows = document.querySelectorAll('#inventoryTable tbody tr');
        
        tableRows.forEach((row, index) => {
            const status = row.querySelector('.badge')?.textContent?.trim();
            const shouldShow = filterValue === 'All Products' || status === filterValue;
            
            if (shouldShow) {
                row.style.display = '';
                row.style.animationDelay = `${index * 50}ms`;
                row.classList.add('animate-fade-in');
            } else {
                row.style.display = 'none';
                row.classList.remove('animate-fade-in');
            }
        });
    }

    refreshData() {
        // Enhanced refresh with loading state
        const refreshBtn = document.querySelector('#refreshTable');
        const originalContent = refreshBtn.innerHTML;
        
        // Show loading state
        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        // Add loading class to table
        const table = document.querySelector('#inventoryTable');
        table.classList.add('loading');
        
        // Simulate API call (replace with actual API call)
        setTimeout(() => {
            // Reset button
            refreshBtn.innerHTML = originalContent;
            refreshBtn.disabled = false;
            
            // Remove loading state
            table.classList.remove('loading');
            
            // Show success notification
            this.showNotification('Data refreshed successfully!', 'success', 3000);
            
            // Trigger actual refresh (this should call your existing loadProducts function)
            if (typeof loadProducts === 'function') {
                loadProducts();
            }
        }, 1500);
    }

    setupPerformanceOptimizations() {
        // Lazy loading for images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
        
        // Debounced resize handler
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    handleResize() {
        // Responsive adjustments
        const sidebar = document.querySelector('.sidebar');
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
        
        // Adjust table for mobile
        const table = document.querySelector('#inventoryTable');
        if (table) {
            table.classList.toggle('table-mobile', window.innerWidth <= 768);
        }
    }

    preloadAssets() {
        // Preload critical assets
        const criticalAssets = [
            '/static/css/modern-inventory.css',
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'
        ];
        
        criticalAssets.forEach(asset => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = asset;
            link.as = 'style';
            document.head.appendChild(link);
        });
    }

    // Utility methods
    formatCurrency(amount, currency = 'PHP') {
        return new Intl.NumberFormat('en-PH', {
            style: 'currency',
            currency: 'PHP',
            minimumFractionDigits: 2
        }).format(amount);
    }

    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
    }

    copyToClipboard(text) {
        return navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            this.showNotification('Failed to copy to clipboard', 'error', 3000);
        });
    }

    downloadData(data, filename, type = 'application/json') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Additional CSS for animations and notifications
const additionalCSS = `
/* Notification System */
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    pointer-events: none;
}

.notification {
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    margin-bottom: 12px;
    min-width: 300px;
    max-width: 400px;
    pointer-events: auto;
    position: relative;
    overflow: hidden;
    border-left: 4px solid;
}

.notification-success { border-left-color: var(--success-500); }
.notification-error { border-left-color: var(--danger-500); }
.notification-warning { border-left-color: var(--warning-500); }
.notification-info { border-left-color: var(--info-500); }

.notification-content {
    display: flex;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
}

.notification-icon {
    font-size: 20px;
    margin-top: 2px;
}

.notification-success .notification-icon { color: var(--success-500); }
.notification-error .notification-icon { color: var(--danger-500); }
.notification-warning .notification-icon { color: var(--warning-500); }
.notification-info .notification-icon { color: var(--info-500); }

.notification-message {
    flex: 1;
    font-weight: 500;
    color: var(--secondary-800);
    line-height: 1.4;
}

.notification-close {
    background: none;
    border: none;
    font-size: 18px;
    color: var(--secondary-400);
    cursor: pointer;
    padding: 0;
    margin-left: 8px;
}

.notification-close:hover {
    color: var(--secondary-600);
}

.notification-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: currentColor;
    opacity: 0.3;
}

.notification-exit {
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.3s ease;
}

@keyframes notificationProgress {
    from { width: 100%; }
    to { width: 0%; }
}

/* Loading animations */
.spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Search highlighting */
.search-highlight {
    background: var(--warning-200);
    color: var(--warning-800);
    padding: 1px 3px;
    border-radius: 3px;
    font-weight: 600;
}

/* Results counter */
.results-counter {
    font-size: 14px;
    color: var(--secondary-500);
    margin-left: auto;
}

/* Form validation styles */
.form-control.is-valid {
    border-color: var(--success-500);
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.form-control.is-invalid {
    border-color: var(--danger-500);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.invalid-feedback {
    color: var(--danger-500);
    font-size: 12px;
    margin-top: 4px;
    display: none;
}

/* Mobile table styles */
.table-mobile {
    font-size: 14px;
}

.table-mobile th,
.table-mobile td {
    padding: 8px 4px;
}

/* Enhanced hover effects */
.btn-modern, .action-btn {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Floating label wrapper */
.form-floating-wrapper {
    position: relative;
}

.form-floating-wrapper.focused .form-label {
    transform: translateY(-12px) scale(0.85);
    color: var(--primary-500);
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

// Initialize the system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.modernInventorySystem = new ModernInventorySystem();
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernInventorySystem;
}
