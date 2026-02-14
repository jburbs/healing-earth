/**
 * Post Navigation Script
 * 
 * Depends on:
 * - nav-data.js (provides postNavData object)
 * - categories.js (provides postCategories object)
 * 
 * This script runs on individual post pages and provides navigation
 * between posts in the archive, organized by category.
 */

/**
 * Extract the category parameter from URL
 * Pattern: ?cat=CATEGORY_NAME
 * Defaults to 'all' if not specified
 */
var getCategoryContext = function() {
  var params = new URLSearchParams(window.location.search);
  var category = params.get('cat');
  return category || 'all';
};

/**
 * Extract the current post folder name from the URL path
 * Pattern: /posts/FOLDER_NAME/index.html
 * Returns: FOLDER_NAME (decoded)
 */
var getCurrentFolder = function() {
  var path = window.location.pathname;
  // Match /posts/FOLDER_NAME/ pattern
  var match = path.match(/\/posts\/([^\/]+)/);
  if (match && match[1]) {
    return decodeURIComponent(match[1]);
  }
  return null;
};

/**
 * Find the previous and next post entries for navigation
 * The postNavData lists are ordered newest-first
 * From a reader's perspective:
 * - "Previous" (←) goes to older posts (higher index / further back)
 * - "Next" (→) goes to newer posts (lower index / more recent)
 */
var getNeighbors = function(folder, category) {
  // Use the specified category, fall back to 'all' if not found
  var list = postNavData[category] || postNavData['all'];
  
  if (!list || !Array.isArray(list)) {
    return { prev: null, next: null };
  }
  
  // Find the current folder in the list (case-insensitive: Netlify lowercases URLs)
  var currentIndex = -1;
  var folderLower = folder.toLowerCase();
  for (var i = 0; i < list.length; i++) {
    if (list[i].folder.toLowerCase() === folderLower) {
      currentIndex = i;
      break;
    }
  }
  
  if (currentIndex === -1) {
    return { prev: null, next: null };
  }
  
  // Previous (older) is the next item in the list (higher index)
  var prevEntry = currentIndex + 1 < list.length ? list[currentIndex + 1] : null;
  
  // Next (newer) is the previous item in the list (lower index)
  var nextEntry = currentIndex - 1 >= 0 ? list[currentIndex - 1] : null;
  
  return { prev: prevEntry, next: nextEntry };
};

/**
 * Build a relative URL to a post
 * Pattern: ../FOLDER_NAME/index.html
 * Append ?cat=CATEGORY if category is not 'all'
 */
var buildPostUrl = function(folder, category) {
  var url = '../' + encodeURIComponent(folder) + '/index.html';
  if (category && category !== 'all') {
    url += '?cat=' + encodeURIComponent(category);
  }
  return url;
};

/**
 * Map category keys to human-readable labels
 */
var getCategoryLabel = function(cat) {
  var labels = {
    'climate': 'Climate Science',
    'solutions': 'Solutions & Technology',
    'policy': 'Policy & Economics',
    'ai': 'AI & Technology',
    'science': 'Science & Methods',
    'notes': 'Notes & Asides',
    'all': 'All Posts'
  };
  return labels[cat] || cat;
};

/**
 * Case-insensitive lookup in postCategories
 * Netlify lowercases URL paths, so folder from URL won't match
 * the mixed-case keys in postCategories directly.
 */
var lookupCategories = function(folder) {
  if (!folder || typeof postCategories === 'undefined') return null;
  // Try direct lookup first (fast path)
  if (postCategories[folder]) return postCategories[folder];
  // Fall back to case-insensitive search
  var folderLower = folder.toLowerCase();
  var keys = Object.keys(postCategories);
  for (var i = 0; i < keys.length; i++) {
    if (keys[i].toLowerCase() === folderLower) {
      return postCategories[keys[i]];
    }
  }
  return null;
};

/**
 * Escape HTML special characters to prevent XSS
 */
var escapeHtml = function(str) {
  if (!str) return '';
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};

/**
 * Render the top navigation strip
 * This is a slim, fixed-position navigation bar at the top of posts
 */
var renderTopStrip = function() {
  var container = document.getElementById('post-nav-top');
  if (!container) {
    container = document.createElement('div');
    container.id = 'post-nav-top';
    document.body.insertBefore(container, document.body.firstChild);
  }
  
  var folder = getCurrentFolder();
  var category = getCategoryContext();
  var neighbors = getNeighbors(folder, category);
  var categoryLabel = getCategoryLabel(category);
  
  var html = '<div class="post-nav-strip">';
  
  // Previous button or empty span
  if (neighbors.prev) {
    var prevUrl = buildPostUrl(neighbors.prev.folder, category);
    var prevTitle = escapeHtml(neighbors.prev.title || 'Previous Post');
    html += '<a href="' + prevUrl + '" class="nav-strip-arrow nav-strip-prev" title="' + prevTitle + '">←</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-prev nav-strip-disabled"></span>';
  }
  
  // Center content: home link and category label
  html += '<div class="nav-strip-center">';
  html += '<a href="../../index.html" class="nav-strip-home">Healing Earth with Technology</a>';
  if (category !== 'all') {
    html += '<span class="nav-strip-category">' + escapeHtml(categoryLabel) + '</span>';
  }
  html += '</div>';
  
  // Next button or empty span
  if (neighbors.next) {
    var nextUrl = buildPostUrl(neighbors.next.folder, category);
    var nextTitle = escapeHtml(neighbors.next.title || 'Next Post');
    html += '<a href="' + nextUrl + '" class="nav-strip-arrow nav-strip-next" title="' + nextTitle + '">→</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-next nav-strip-disabled"></span>';
  }
  
  html += '</div>';
  
  container.innerHTML = html;
};

/**
 * Render the bottom navigation section
 * Includes previous/next cards and category badges
 */
var renderBottomNav = function() {
  var container = document.getElementById('post-nav-bottom');
  if (!container) {
    container = document.createElement('div');
    container.id = 'post-nav-bottom';
    document.body.appendChild(container);
  }
  
  var folder = getCurrentFolder();
  var category = getCategoryContext();
  var neighbors = getNeighbors(folder, category);
  var categoryLabel = getCategoryLabel(category);
  
  var html = '<nav class="post-nav-bottom">';
  
  // Navigation cards section
  html += '<div class="post-nav-cards">';
  
  // Previous card
  if (neighbors.prev) {
    var prevUrl = buildPostUrl(neighbors.prev.folder, category);
    var prevTitle = escapeHtml(neighbors.prev.title || 'Previous Post');
    var prevDate = escapeHtml(neighbors.prev.date || '');
    html += '<a href="' + prevUrl + '" class="post-nav-card post-nav-card-prev">';
    html += '<span class="nav-card-direction">← Previous</span>';
    html += '<span class="nav-card-title">' + prevTitle + '</span>';
    if (prevDate) {
      html += '<span class="nav-card-date">' + prevDate + '</span>';
    }
    html += '</a>';
  } else {
    html += '<div class="post-nav-card post-nav-card-empty"></div>';
  }
  
  // Next card
  if (neighbors.next) {
    var nextUrl = buildPostUrl(neighbors.next.folder, category);
    var nextTitle = escapeHtml(neighbors.next.title || 'Next Post');
    var nextDate = escapeHtml(neighbors.next.date || '');
    html += '<a href="' + nextUrl + '" class="post-nav-card post-nav-card-next">';
    html += '<span class="nav-card-direction">Next →</span>';
    html += '<span class="nav-card-title">' + nextTitle + '</span>';
    if (nextDate) {
      html += '<span class="nav-card-date">' + nextDate + '</span>';
    }
    html += '</a>';
  } else {
    html += '<div class="post-nav-card post-nav-card-empty"></div>';
  }
  
  html += '</div>';
  
  // Categories section
  html += '<div class="post-nav-categories">';
  html += '<span class="post-nav-categories-label">Filed under:</span>';
  
  var postCats = lookupCategories(folder);
  if (postCats && Array.isArray(postCats)) {
    for (var i = 0; i < postCats.length; i++) {
      var cat = postCats[i];
      var catLabel = getCategoryLabel(cat);
      var catUrl = '../../index.html?cat=' + encodeURIComponent(cat);
      html += '<a href="' + catUrl + '" class="category-badge ' + escapeHtml(cat) + '">' + escapeHtml(catLabel) + '</a>';
    }
  }
  
  html += '</div>';
  html += '</nav>';
  
  container.innerHTML = html;
};

/**
 * Initialize the post navigation
 * Only runs on post pages (URL contains /posts/)
 */
var init = function() {
  // Only run on post pages
  if (window.location.pathname.indexOf('/posts/') === -1) {
    return;
  }
  
  // Verify required data objects are available
  if (typeof postNavData === 'undefined' || typeof postCategories === 'undefined') {
    console.warn('post-nav.js: Required data objects (postNavData, postCategories) not found. Make sure nav-data.js and categories.js are loaded first.');
    return;
  }
  
  // Render navigation components
  renderTopStrip();
  renderBottomNav();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
