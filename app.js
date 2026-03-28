// App controller for Healing Earth with Technology
// Handles tabs, category filtering, series view, and search integration

document.addEventListener('DOMContentLoaded', function() {
    const searchBox = document.getElementById('searchBox');
    const postList = document.getElementById('postList');
    const seriesView = document.getElementById('seriesView');
    const tabBar = document.getElementById('tabBar');

    if (!postList || !tabBar) return;

    // Store all post LI elements
    const allPosts = Array.from(postList.querySelectorAll('li[data-folder]'));

    let currentCategory = 'all';
    let isSearching = false;

    // --- Add popularity data to posts ---
    function addPopularityData() {
        if (typeof postPopularity === 'undefined') return;

        allPosts.forEach(function(li) {
            const folder = li.getAttribute('data-folder');
            const rank = postPopularity[folder] || 999;
            li.setAttribute('data-popularity', rank);
        });
    }

    // --- Sort posts chronologically (oldest first) ---
    function sortByDate(postsToSort) {
        return postsToSort.sort(function(a, b) {
            const folderA = a.getAttribute('data-folder') || '';
            const folderB = b.getAttribute('data-folder') || '';
            return folderA.localeCompare(folderB);
        });
    }

    // --- Category Badges ---
    function renderBadges() {
        if (typeof postCategories === 'undefined') return;

        const categoryLabels = {
            climate: 'Climate',
            solutions: 'Solutions',
            policy: 'Policy',
            ai: 'AI',
            science: 'Science',
            notes: 'Notes'
        };

        allPosts.forEach(function(li) {
            const folder = li.getAttribute('data-folder');
            const badgeContainer = li.querySelector('.category-badges');
            if (!badgeContainer || !postCategories[folder]) return;

            const cats = postCategories[folder];
            const badges = cats.map(function(cat) {
                const label = categoryLabels[cat] || cat;
                return '<a href="#" class="category-badge ' + cat + '" data-filter-category="' + cat + '">' + label + '</a>';
            });
            badgeContainer.innerHTML = badges.join(' ');
        });
    }

    // --- Tab Filtering ---
    function filterByCategory(category, options) {
        var opts = options || {};
        currentCategory = category;

        // Update active tab - use .tab-item class
        tabBar.querySelectorAll('.tab-item').forEach(function(tab) {
            tab.classList.toggle('active', tab.getAttribute('data-category') === category);
        });

        // Show/hide series view
        if (category === 'series') {
            seriesView.style.display = 'block';
            postList.style.display = 'none';
            if (searchBox) searchBox.style.display = 'none';
            renderSeriesView();
            return;
        } else {
            seriesView.style.display = 'none';
            postList.style.display = '';
            if (searchBox) searchBox.style.display = '';
        }

        // Clear search when switching tabs (but NOT when restoring from short query)
        if (searchBox && !opts.preserveSearch) {
            searchBox.value = '';
            isSearching = false;
        }

        // Hide search results container when switching tabs
        var searchResultsDiv = document.getElementById('searchResults');
        if (searchResultsDiv) {
            searchResultsDiv.style.display = 'none';
            searchResultsDiv.innerHTML = '';
        }

        // Filter posts and update links with category context
        var visiblePosts;
        if (category === 'all') {
            visiblePosts = allPosts.filter(function(li) {
                li.style.display = '';
                // Remove category param from links
                var link = li.querySelector('.post-list-title a');
                if (link) {
                    link.href = link.href.split('?')[0];
                }
                return true;
            });
        } else {
            visiblePosts = allPosts.filter(function(li) {
                var folder = li.getAttribute('data-folder');
                var cats = (typeof postCategories !== 'undefined' && postCategories[folder]) || [];
                var visible = cats.indexOf(category) !== -1;
                li.style.display = visible ? '' : 'none';
                // Add category context to visible post links
                var link = li.querySelector('.post-list-title a');
                if (link && visible) {
                    link.href = link.href.split('?')[0] + '?cat=' + encodeURIComponent(category);
                }
                return visible;
            });
        }

        // Sort visible posts by popularity and re-render
        var sortedPosts = sortByDate(visiblePosts);
        sortedPosts.forEach(function(li) {
            postList.appendChild(li);
        });

        updatePostCount();
    }

    function updatePostCount() {
        var visible = allPosts.filter(function(li) { return li.style.display !== 'none'; }).length;
        var existing = postList.querySelector('.filter-count');
        if (existing) existing.remove();

        if (currentCategory !== 'all' && !isSearching) {
            var countEl = document.createElement('li');
            countEl.className = 'filter-count';
            countEl.style.cssText = 'padding: 0.5rem 0 1rem; font-family: var(--font-sans); font-size: 0.85rem; color: var(--text-secondary); border-bottom: 1px solid var(--border-color); list-style: none;';
            countEl.textContent = visible + ' post' + (visible === 1 ? '' : 's');
            postList.insertBefore(countEl, postList.firstChild);
        }
    }

    // --- Series View ---
    function renderSeriesView() {
        if (typeof seriesData === 'undefined') {
            seriesView.innerHTML = '<p>Series data not available.</p>';
            return;
        }

        var html = '<div class="series-grid">';
        var keys = Object.keys(seriesData);

        keys.forEach(function(key) {
            var s = seriesData[key];
            var partCount = s.parts ? s.parts.length : 0;

            html += '<div class="series-card">';
            html += '<h3 class="series-card-title">' + s.title + '</h3>';
            html += '<p class="series-card-description">' + s.description + '</p>';
            html += '<p class="series-card-count">' + partCount + ' part' + (partCount === 1 ? '' : 's') + '</p>';
            html += '<div class="series-parts">';

            if (s.parts) {
                s.parts.forEach(function(part) {
                    var href = 'posts/' + part.folder + '/index.html?cat=series';
                    html += '<a href="' + href + '" class="series-part-link">';
                    html += '<span class="part-num">Part ' + part.partNum + '</span> ';
                    html += '<span class="part-title">' + part.title + '</span>';
                    html += '</a>';
                });
            }

            html += '</div></div>';
        });

        html += '</div>';
        seriesView.innerHTML = html;
    }

    // --- Search ---
    // Create a persistent results container OUTSIDE postList so we never
    // destroy the search input's DOM ancestry during rendering.
    // This fixes the iOS mobile bug where keystrokes get cleared.
    var searchResultsDiv = document.createElement('div');
    searchResultsDiv.id = 'searchResults';
    searchResultsDiv.style.display = 'none';
    postList.parentNode.insertBefore(searchResultsDiv, postList.nextSibling);

    if (searchBox && typeof searchPosts === 'function') {
        var debounceTimer;

        searchBox.addEventListener('input', function() {
            var query = this.value.trim();  // capture immediately — not inside setTimeout (fixes stale-value race)
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {

                if (!query || query.length < 2) {
                    isSearching = false;
                    // Hide search results, restore post list
                    searchResultsDiv.style.display = 'none';
                    searchResultsDiv.innerHTML = '';
                    postList.style.display = '';
                    // Re-append all original posts (they were never destroyed)
                    allPosts.forEach(function(li) {
                        li.style.display = '';
                        postList.appendChild(li);
                    });
                    renderBadges();
                    filterByCategory(currentCategory, { preserveSearch: true });
                    return;
                }

                isSearching = true;
                var results = searchPosts(query);

                // Hide original post list, show results in separate container
                postList.style.display = 'none';
                searchResultsDiv.style.display = 'block';

                if (!results || results.length === 0) {
                    searchResultsDiv.innerHTML = '<ul class="post-list"><li class="search-no-results" style="padding: 2rem 0; color: var(--text-secondary); list-style: none;">No posts found matching \u201c' + escapeHtml(query) + '\u201d</li></ul>';
                    return;
                }

                // Build search results HTML
                var totalMatches = results.reduce(function(sum, p) { return sum + p.matchCount; }, 0);

                var html = '<ul class="post-list">';
                html += '<li class="search-results-header" style="padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); font-family: var(--font-sans); font-size: 0.85rem; color: var(--text-secondary); list-style: none;">';
                html += '<strong>' + results.length + '</strong> post' + (results.length === 1 ? '' : 's');
                html += ' with <strong>' + totalMatches + '</strong> match' + (totalMatches === 1 ? '' : 'es');
                html += ' for \u201c' + escapeHtml(query) + '\u201d</li>';

                results.forEach(function(post) {
                    var snippet = getContextSnippet(post.content, query);
                    var matchLabel = post.matchCount === 1 ? '1 match' : post.matchCount + ' matches';
                    html += '<li style="border-bottom: 1px solid var(--border-color); padding: 1.75rem 0;">';
                    html += '<h3 class="post-list-title"><a href="' + post.href + '">' + highlightMatch(post.title, query) + '</a></h3>';
                    html += '<div class="post-list-info"><span class="post-list-meta">' + post.date + ' \u00b7 ' + matchLabel + '</span></div>';
                    html += '<p class="post-list-excerpt">' + snippet + '</p>';
                    html += '</li>';
                });

                html += '</ul>';
                searchResultsDiv.innerHTML = html;

            }, 250);
        });
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // --- Tab click handlers ---
    tabBar.addEventListener('click', function(e) {
        var tabItem = e.target.closest('.tab-item');
        if (!tabItem) return;
        e.preventDefault();
        var category = tabItem.getAttribute('data-category');
        filterByCategory(category);
    });

    // --- Badge click handlers (delegate from postList) ---
    postList.addEventListener('click', function(e) {
        var badge = e.target.closest('[data-filter-category]');
        if (!badge) return;
        e.preventDefault();
        var category = badge.getAttribute('data-filter-category');
        filterByCategory(category);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // --- Topic card click handlers ---
    document.querySelectorAll('.topic-card[data-topic]').forEach(function(card) {
        card.addEventListener('click', function(e) {
            e.preventDefault();
            var topic = card.getAttribute('data-topic');
            filterByCategory(topic);
            var archive = document.getElementById('archive');
            if (archive) {
                archive.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- Initialize ---
    addPopularityData();
    renderBadges();
    filterByCategory('all'); // Load with default 'all' category, sorted chronologically

    // Handle URL hash for direct category links
    if (window.location.hash) {
        var hashCat = new URLSearchParams(window.location.hash.replace('#', '?')).get('cat');
        if (hashCat) {
            filterByCategory(hashCat);
        }
    }
});