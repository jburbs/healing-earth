/**
 * search-universal.js
 * 
 * Provides universal search functionality across all pages (post pages, about page, homepage).
 * Depends on search.js being loaded first, which provides:
 * - searchPosts(query) function
 * - highlightMatch(text, query) function  
 * - getContextSnippet(content, query) function
 * - searchIndex array
 */

var UniversalSearch = (function() {
  // Configuration
  var CONFIG = {
    DEBOUNCE_DELAY: 200,
    MIN_SEARCH_LENGTH: 2,
    MAX_RESULTS: 5
  };

  // State
  var state = {
    debounceTimer: null,
    dropdownOpen: false,
    navSearchBox: null,
    searchDropdown: null,
    pageType: 'homepage' // 'post' or 'about' or 'homepage'
  };

  /**
   * Determine the current page type from the URL
   */
  function getPageType() {
    var pathname = window.location.pathname;
    if (pathname.indexOf('/posts/') !== -1) {
      return 'post';
    } else if (pathname.indexOf('about.html') !== -1) {
      return 'about';
    }
    return 'homepage';
  }

  /**
   * Get the base URL path for navigation links
   */
  function getBasePathForLinks() {
    if (state.pageType === 'post') {
      return '../../';
    } else if (state.pageType === 'about') {
      return '';
    }
    return '';
  }

  /**
   * Get the search results URL
   */
  function getSearchResultsUrl(query) {
    var basePath = getBasePathForLinks();
    var searchUrl = basePath + 'index.html?q=' + encodeURIComponent(query);
    return searchUrl;
  }

  /**
   * Create and position the dropdown element
   */
  function createDropdown() {
    var dropdown = document.createElement('div');
    dropdown.id = 'searchDropdown';
    dropdown.className = 'search-dropdown';
    dropdown.style.position = 'absolute';
    dropdown.style.top = '100%';
    dropdown.style.left = '0';
    dropdown.style.zIndex = '1000';
    dropdown.style.minWidth = '300px';
    dropdown.style.marginTop = '8px';
    dropdown.style.backgroundColor = '#fff';
    dropdown.style.border = '1px solid #ddd';
    dropdown.style.borderRadius = '4px';
    dropdown.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
    dropdown.style.maxHeight = '400px';
    dropdown.style.overflowY = 'auto';
    return dropdown;
  }

  /**
   * Render search results in the dropdown
   */
  function renderResults(results, query) {
    // Clear existing dropdown
    if (state.searchDropdown) {
      state.searchDropdown.innerHTML = '';
    } else {
      state.searchDropdown = createDropdown();
      // Position relative to the search box
      var navSearchBox = state.navSearchBox;
      navSearchBox.parentNode.style.position = 'relative';
      navSearchBox.parentNode.appendChild(state.searchDropdown);
    }

    // Render result items (max 5)
    var displayResults = results.slice(0, CONFIG.MAX_RESULTS);
    displayResults.forEach(function(result) {
      var resultLink = document.createElement('a');
      resultLink.href = (state.pageType === 'post' ? '../../' : '') + result.href;
      resultLink.className = 'search-dropdown-item';
      resultLink.style.display = 'block';
      resultLink.style.padding = '12px 16px';
      resultLink.style.borderBottom = '1px solid #f0f0f0';
      resultLink.style.textDecoration = 'none';
      resultLink.style.color = '#333';
      resultLink.style.transition = 'background-color 0.15s';

      // Hover effect
      resultLink.onmouseover = function() {
        this.style.backgroundColor = '#f9f9f9';
      };
      resultLink.onmouseout = function() {
        this.style.backgroundColor = 'transparent';
      };

      var titleDiv = document.createElement('div');
      titleDiv.className = 'search-dropdown-title';
      titleDiv.style.fontWeight = '500';
      titleDiv.style.marginBottom = '4px';
      titleDiv.style.lineHeight = '1.4';
      // Use the highlightMatch function from search.js if available
      titleDiv.innerHTML = typeof highlightMatch !== 'undefined' 
        ? highlightMatch(result.title, query)
        : result.title;

      var dateDiv = document.createElement('div');
      dateDiv.className = 'search-dropdown-date';
      dateDiv.style.fontSize = '0.85em';
      dateDiv.style.color = '#999';
      dateDiv.textContent = result.date || '';

      resultLink.appendChild(titleDiv);
      resultLink.appendChild(dateDiv);
      state.searchDropdown.appendChild(resultLink);
    });

    // Add "View all results" link if there are more results
    if (results.length > CONFIG.MAX_RESULTS) {
      var moreLink = document.createElement('a');
      moreLink.href = getSearchResultsUrl(query);
      moreLink.className = 'search-dropdown-more';
      moreLink.style.display = 'block';
      moreLink.style.padding = '12px 16px';
      moreLink.style.textAlign = 'center';
      moreLink.style.color = '#0066cc';
      moreLink.style.textDecoration = 'none';
      moreLink.style.fontSize = '0.95em';
      moreLink.style.borderTop = '1px solid #f0f0f0';
      moreLink.style.transition = 'background-color 0.15s';
      moreLink.onmouseover = function() {
        this.style.backgroundColor = '#f9f9f9';
      };
      moreLink.onmouseout = function() {
        this.style.backgroundColor = 'transparent';
      };
      moreLink.textContent = 'View all ' + results.length + ' results →';
      state.searchDropdown.appendChild(moreLink);
    }

    state.dropdownOpen = true;
  }

  /**
   * Close the search dropdown
   */
  function closeDropdown() {
    if (state.searchDropdown && state.dropdownOpen) {
      state.searchDropdown.style.display = 'none';
      state.dropdownOpen = false;
    }
  }

  /**
   * Open the search dropdown
   */
  function openDropdown() {
    if (state.searchDropdown) {
      state.searchDropdown.style.display = 'block';
      state.dropdownOpen = true;
    }
  }

  /**
   * Handle search input with debouncing
   */
  function handleSearchInput(query) {
    // Clear existing debounce timer
    if (state.debounceTimer) {
      clearTimeout(state.debounceTimer);
    }

    // Close dropdown if query is too short
    if (query.length < CONFIG.MIN_SEARCH_LENGTH) {
      closeDropdown();
      return;
    }

    // Debounce the search
    state.debounceTimer = setTimeout(function() {
      if (typeof searchPosts === 'undefined') {
        console.warn('search.js not loaded - searchPosts() not available');
        return;
      }

      var results = searchPosts(query);
      if (results.length > 0) {
        renderResults(results, query);
        openDropdown();
      } else {
        closeDropdown();
      }
    }, CONFIG.DEBOUNCE_DELAY);
  }

  /**
   * Handle clicks outside the search box/dropdown
   */
  function handleDocumentClick(e) {
    if (!state.navSearchBox) return;

    var isClickInside = state.navSearchBox.contains(e.target) || 
                        (state.searchDropdown && state.searchDropdown.contains(e.target));

    if (!isClickInside) {
      closeDropdown();
    }
  }

  /**
   * Handle Escape key
   */
  function handleKeyDown(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
      closeDropdown();
      if (state.navSearchBox) {
        state.navSearchBox.blur();
      }
    }
  }

  /**
   * Initialize universal search on non-homepage
   */
  function initNavSearch() {
    state.navSearchBox = document.getElementById('navSearchBox');
    if (!state.navSearchBox) return;

    // Wire up input event
    state.navSearchBox.addEventListener('input', function(e) {
      var query = e.target.value.trim();
      handleSearchInput(query);
    });

    // Wire up focus event to create dropdown if needed
    state.navSearchBox.addEventListener('focus', function() {
      var query = state.navSearchBox.value.trim();
      if (query.length >= CONFIG.MIN_SEARCH_LENGTH) {
        if (typeof searchPosts !== 'undefined') {
          var results = searchPosts(query);
          if (results.length > 0) {
            renderResults(results, query);
            openDropdown();
          }
        }
      }
    });

    // Close dropdown when cleared
    state.navSearchBox.addEventListener('blur', function() {
      // Delay closing to allow clicks on dropdown items
      setTimeout(closeDropdown, 200);
    });
  }

  /**
   * Initialize search on homepage
   */
  function initHomepageSearch() {
    state.navSearchBox = document.getElementById('navSearchBox');
    var mainSearchBox = document.getElementById('searchBox');

    if (!state.navSearchBox || !mainSearchBox) return;

    // Sync nav search box to main search box
    state.navSearchBox.addEventListener('input', function(e) {
      mainSearchBox.value = e.target.value;
      // Trigger the main search box's input event
      var inputEvent = new Event('input', { bubbles: true });
      mainSearchBox.dispatchEvent(inputEvent);
    });

    // Optionally sync main search box back to nav
    mainSearchBox.addEventListener('input', function(e) {
      state.navSearchBox.value = e.target.value;
    });
  }

  /**
   * Initialize universal search
   */
  function init() {
    state.pageType = getPageType();

    if (state.pageType === 'homepage') {
      initHomepageSearch();
    } else {
      // Post page or about page
      initNavSearch();
    }

    // Add global event listeners
    document.addEventListener('click', handleDocumentClick);
    document.addEventListener('keydown', handleKeyDown);
  }

  // Public API
  return {
    init: init
  };
})();

/**
 * Initialize when DOM is ready
 */
function initUniversalSearch() {
  UniversalSearch.init();
}

// Hook into DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initUniversalSearch);
} else {
  // DOM already loaded
  initUniversalSearch();
}
