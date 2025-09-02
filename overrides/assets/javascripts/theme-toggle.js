// Enhanced theme toggle functionality
(function() {
  'use strict';

  // Theme management class
  class ThemeManager {
    constructor() {
      this.storageKey = 'ecomate-theme-preference';
      this.init();
    }

    init() {
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setup());
      } else {
        this.setup();
      }
    }

    setup() {
      this.loadSavedTheme();
      this.setupToggleListeners();
      this.setupSystemThemeListener();
    }

    // Load theme preference from localStorage
    loadSavedTheme() {
      const savedTheme = localStorage.getItem(this.storageKey);
      if (savedTheme) {
        this.setTheme(savedTheme);
      }
    }

    // Set theme and save preference
    setTheme(scheme) {
      const body = document.body;
      const currentScheme = body.getAttribute('data-md-color-scheme');
      
      if (currentScheme !== scheme) {
        // Add transition class
        body.classList.add('theme-switching');
        
        // Set new theme
        body.setAttribute('data-md-color-scheme', scheme);
        
        // Save preference
        localStorage.setItem(this.storageKey, scheme);
        
        // Remove transition class after animation
        setTimeout(() => {
          body.classList.remove('theme-switching');
        }, 300);
        
        // Dispatch custom event
        this.dispatchThemeChangeEvent(scheme);
      }
    }

    // Setup toggle button listeners
    setupToggleListeners() {
      // Listen for palette toggle clicks
      document.addEventListener('click', (event) => {
        const toggle = event.target.closest('[data-md-toggle="palette"]');
        if (toggle) {
          // Small delay to let Material's handler run first
          setTimeout(() => {
            const currentScheme = document.body.getAttribute('data-md-color-scheme');
            localStorage.setItem(this.storageKey, currentScheme);
            this.dispatchThemeChangeEvent(currentScheme);
          }, 50);
        }
      });
    }

    // Listen for system theme changes
    setupSystemThemeListener() {
      if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addEventListener('change', (e) => {
          // Only auto-switch if no manual preference is saved
          const savedTheme = localStorage.getItem(this.storageKey);
          if (!savedTheme) {
            const newScheme = e.matches ? 'slate' : 'default';
            this.setTheme(newScheme);
          }
        });
      }
    }

    // Dispatch custom theme change event
    dispatchThemeChangeEvent(scheme) {
      const event = new CustomEvent('themeChanged', {
        detail: { scheme: scheme }
      });
      document.dispatchEvent(event);
    }

    // Public method to manually set theme
    switchTheme(scheme) {
      this.setTheme(scheme);
    }

    // Get current theme
    getCurrentTheme() {
      return document.body.getAttribute('data-md-color-scheme') || 'default';
    }

    // Reset to system preference
    resetToSystemTheme() {
      localStorage.removeItem(this.storageKey);
      const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      const systemScheme = systemPrefersDark ? 'slate' : 'default';
      this.setTheme(systemScheme);
    }
  }

  // Initialize theme manager
  const themeManager = new ThemeManager();

  // Expose to global scope for debugging/external use
  window.EcoMateTheme = {
    switch: (scheme) => themeManager.switchTheme(scheme),
    current: () => themeManager.getCurrentTheme(),
    reset: () => themeManager.resetToSystemTheme()
  };

  // Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + T)
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'T') {
      event.preventDefault();
      const currentTheme = themeManager.getCurrentTheme();
      const newTheme = currentTheme === 'slate' ? 'default' : 'slate';
      themeManager.switchTheme(newTheme);
    }
  });

  // Add theme change listener for analytics or other integrations
  document.addEventListener('themeChanged', (event) => {
    console.log('Theme changed to:', event.detail.scheme);
    // Add any additional theme change handling here
  });

})();