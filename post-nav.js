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
  var match = path.match(/\/posts\/([^\/]+)/);
  if (match && match[1]) {
    return decodeURIComponent(match[1]);
  }
  return null;
};

/**
 * Find the previous and next post entries for navigation
 * The postNavData lists are ordered newest-first
 * - "Previous" (←) goes to older posts (higher index)
 * - "Next" (→) goes to newer posts (lower index)
 */
var getNeighbors = function(folder, category) {
  var list = postNavData[category] || postNavData['all'];

  if (!list || !Array.isArray(list)) {
    return { prev: null, next: null };
  }

  // Case-insensitive: Netlify lowercases URLs
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

  var prevEntry = currentIndex + 1 < list.length ? list[currentIndex + 1] : null;
  var nextEntry = currentIndex - 1 >= 0 ? list[currentIndex - 1] : null;

  return { prev: prevEntry, next: nextEntry };
};

/**
 * Build a relative URL to a post
 */
var buildPostUrl = function(folder, category) {
  var url = '../' + encodeURIComponent(folder) + '/index.html';
  if (category && category !== 'all') {
    url += '?cat=' + encodeURIComponent(category);
  }
  return url;
};

/**
 * Short category labels for compact display
 */
var getCategoryShort = function(cat) {
  var labels = {
    'climate': 'Climate',
    'solutions': 'Solutions',
    'policy': 'Policy',
    'ai': 'AI',
    'science': 'Science',
    'notes': 'Notes',
    'all': 'All'
  };
  return labels[cat] || cat;
};

/**
 * Full category labels
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
 */
var lookupCategories = function(folder) {
  if (!folder || typeof postCategories === 'undefined') return null;
  if (postCategories[folder]) return postCategories[folder];
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
 * Escape HTML special characters
 */
var escapeHtml = function(str) {
  if (!str) return '';
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};

/**
 * Render the top navigation strip
 * Compact: ← prev title | Category | next title →
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
  var catShort = getCategoryShort(category);

  var html = '<div class="post-nav-strip">';

  // Previous (older)
  if (neighbors.prev) {
    var prevUrl = buildPostUrl(neighbors.prev.folder, category);
    var prevTitle = escapeHtml(neighbors.prev.title || 'Older');
    html += '<a href="' + prevUrl + '" class="nav-strip-arrow nav-strip-prev" title="' + prevTitle + '">← ' + prevTitle + '</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-prev nav-strip-disabled"></span>';
  }

  // Center: category badge linking to archive
  if (category !== 'all') {
    html += '<a href="../../index.html?cat=' + encodeURIComponent(category) + '" class="nav-strip-cat">' + escapeHtml(catShort) + '</a>';
  } else {
    html += '<a href="../../index.html" class="nav-strip-cat">Archive</a>';
  }

  // Next (newer)
  if (neighbors.next) {
    var nextUrl = buildPostUrl(neighbors.next.folder, category);
    var nextTitle = escapeHtml(neighbors.next.title || 'Newer');
    html += '<a href="' + nextUrl + '" class="nav-strip-arrow nav-strip-next" title="' + nextTitle + '">' + nextTitle + ' →</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-next nav-strip-disabled"></span>';
  }

  html += '</div>';

  container.innerHTML = html;
};

/**
 * Render the bottom navigation section
 * Includes: arrow strip (duplicate of top) + prev/next cards + category badges
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
  var catShort = getCategoryShort(category);

  var html = '<nav class="post-nav-bottom">';

  // Arrow strip at bottom (mirrors top)
  html += '<div class="post-nav-strip post-nav-strip-bottom">';

  if (neighbors.prev) {
    var prevUrl = buildPostUrl(neighbors.prev.folder, category);
    var prevTitle = escapeHtml(neighbors.prev.title || 'Older');
    html += '<a href="' + prevUrl + '" class="nav-strip-arrow nav-strip-prev" title="' + prevTitle + '">← ' + prevTitle + '</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-prev nav-strip-disabled"></span>';
  }

  if (category !== 'all') {
    html += '<a href="../../index.html?cat=' + encodeURIComponent(category) + '" class="nav-strip-cat">' + escapeHtml(catShort) + '</a>';
  } else {
    html += '<a href="../../index.html" class="nav-strip-cat">Archive</a>';
  }

  if (neighbors.next) {
    var nextUrl = buildPostUrl(neighbors.next.folder, category);
    var nextTitle = escapeHtml(neighbors.next.title || 'Newer');
    html += '<a href="' + nextUrl + '" class="nav-strip-arrow nav-strip-next" title="' + nextTitle + '">' + nextTitle + ' →</a>';
  } else {
    html += '<span class="nav-strip-arrow nav-strip-next nav-strip-disabled"></span>';
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
 */
var init = function() {
  if (window.location.pathname.indexOf('/posts/') === -1) {
    return;
  }

  if (typeof postNavData === 'undefined' || typeof postCategories === 'undefined') {
    console.warn('post-nav.js: Required data objects not found.');
    return;
  }

  renderTopStrip();
  renderBottomNav();
};

document.addEventListener('DOMContentLoaded', init);
