document.addEventListener('DOMContentLoaded', function() {
    // Get the data table
    const dataTable = document.querySelector('.data-table');
    if (!dataTable) return;
    
    // Create wrapper elements
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-wrapper';
    
    const tableContainer = document.createElement('div');
    tableContainer.className = 'table-container';
    
    // Insert the wrappers
    dataTable.parentNode.insertBefore(tableWrapper, dataTable);
    tableWrapper.appendChild(tableContainer);
    tableContainer.appendChild(dataTable);
    
    // Get all rows and headers
    let allRows = Array.from(dataTable.querySelectorAll('tbody tr'));
    let filteredRows = [...allRows];
    const headers = Array.from(dataTable.querySelectorAll('thead th')).map(th => th.textContent.trim());
    
    // Pagination variables
    let rowsPerPage = 10;
    let currentPage = 1;
    let totalPages = Math.ceil(filteredRows.length / rowsPerPage);
    
    // Search and filter state
    let activeFilters = {};
    let globalSearchTerm = '';
    
    // Create pagination controls
    const paginationControls = document.getElementById('pagination-controls');
    if (paginationControls) {
        // Function to update pagination UI
        function updatePaginationUI() {
            totalPages = Math.ceil(filteredRows.length / rowsPerPage);
            
            paginationControls.innerHTML = `
                <div class="pagination">
                    <button id="first-page" ${currentPage === 1 ? 'disabled' : ''}><i class="fas fa-angle-double-left"></i> First</button>
                    <button id="prev-page" ${currentPage === 1 ? 'disabled' : ''}><i class="fas fa-angle-left"></i> Previous</button>
                    
                    <div class="page-info">
                        <span class="page-numbers">
                            Page <input type="number" id="page-input" value="${currentPage}" min="1" max="${totalPages}"> of ${totalPages}
                        </span>
                    </div>
                    
                    <button id="next-page" ${currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}>Next <i class="fas fa-angle-right"></i></button>
                    <button id="last-page" ${currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}>Last <i class="fas fa-angle-double-right"></i></button>
                    
                    <div class="per-page-selector">
                        <label for="rows-per-page">Show:</label>
                        <select id="rows-per-page">
                            <option value="5" ${rowsPerPage === 5 ? 'selected' : ''}>5</option>
                            <option value="10" ${rowsPerPage === 10 ? 'selected' : ''}>10</option>
                            <option value="25" ${rowsPerPage === 25 ? 'selected' : ''}>25</option>
                            <option value="50" ${rowsPerPage === 50 ? 'selected' : ''}>50</option>
                            <option value="100" ${rowsPerPage === 100 ? 'selected' : ''}>100</option>
                        </select>
                        <span>entries</span>
                    </div>
                </div>
                
                <div class="table-info">
                    Showing ${filteredRows.length === 0 ? 0 : ((currentPage - 1) * rowsPerPage + 1)} to ${Math.min(currentPage * rowsPerPage, filteredRows.length)} of ${filteredRows.length} entries
                    ${Object.keys(activeFilters).length > 0 || globalSearchTerm ? ` (filtered from ${allRows.length} total entries)` : ''}
                </div>
            `;
            
            attachPaginationEvents();
        }
        
        // Function to display rows for current page
        function displayRows() {
            // Hide all rows first
            allRows.forEach(row => {
                row.style.display = 'none';
            });
            
            // Show only filtered rows for current page
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            
            filteredRows.slice(start, end).forEach(row => {
                row.style.display = '';
            });
            
            updatePaginationUI();
        }
        
        // Function to attach pagination event listeners
        function attachPaginationEvents() {
            // First page button
            const firstBtn = document.getElementById('first-page');
            if (firstBtn) {
                firstBtn.addEventListener('click', () => {
                    currentPage = 1;
                    displayRows();
                });
            }
            
            // Previous page button
            const prevBtn = document.getElementById('prev-page');
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    if (currentPage > 1) {
                        currentPage--;
                        displayRows();
                    }
                });
            }
            
            // Next page button
            const nextBtn = document.getElementById('next-page');
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    if (currentPage < totalPages) {
                        currentPage++;
                        displayRows();
                    }
                });
            }
            
            // Last page button
            const lastBtn = document.getElementById('last-page');
            if (lastBtn) {
                lastBtn.addEventListener('click', () => {
                    currentPage = totalPages || 1;
                    displayRows();
                });
            }
            
            // Page input field
            const pageInput = document.getElementById('page-input');
            if (pageInput) {
                pageInput.addEventListener('change', (e) => {
                    let newPage = parseInt(e.target.value);
                    if (newPage >= 1 && newPage <= totalPages) {
                        currentPage = newPage;
                        displayRows();
                    } else {
                        e.target.value = currentPage;
                    }
                });
                
                pageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        let newPage = parseInt(e.target.value);
                        if (newPage >= 1 && newPage <= totalPages) {
                            currentPage = newPage;
                            displayRows();
                        } else {
                            e.target.value = currentPage;
                        }
                    }
                });
            }
            
            // Rows per page selector
            const rowsSelect = document.getElementById('rows-per-page');
            if (rowsSelect) {
                rowsSelect.addEventListener('change', (e) => {
                    rowsPerPage = parseInt(e.target.value);
                    totalPages = Math.ceil(filteredRows.length / rowsPerPage);
                    
                    // Adjust current page if necessary
                    if (currentPage > totalPages) {
                        currentPage = totalPages || 1;
                    }
                    
                    displayRows();
                });
            }
        }
        
        // Initial setup
        updatePaginationUI();
        displayRows();
    }
    
    // Function to apply all filters
    function applyFilters() {
        filteredRows = allRows.filter(row => {
            const cells = Array.from(row.cells);
            
            // Check global search
            if (globalSearchTerm) {
                const rowText = cells.map(cell => cell.textContent.toLowerCase()).join(' ');
                if (!rowText.includes(globalSearchTerm.toLowerCase())) {
                    return false;
                }
            }
            
            // Check category-specific filters
            for (const [columnIndex, filterValue] of Object.entries(activeFilters)) {
                if (filterValue && cells[columnIndex]) {
                    const cellText = cells[columnIndex].textContent.toLowerCase();
                    if (!cellText.includes(filterValue.toLowerCase())) {
                        return false;
                    }
                }
            }
            
            return true;
        });
        
        // Reset to first page and update display
        currentPage = 1;
        totalPages = Math.ceil(filteredRows.length / rowsPerPage);
        displayRows();
        
        // Update active filters display
        updateActiveFiltersDisplay();
    }
    
    // Function to update active filters display
    function updateActiveFiltersDisplay() {
        const existingFiltersDisplay = document.querySelector('.active-filters');
        if (existingFiltersDisplay) {
            existingFiltersDisplay.remove();
        }
        
        const hasActiveFilters = Object.keys(activeFilters).some(key => activeFilters[key]) || globalSearchTerm;
        
        if (hasActiveFilters) {
            const filtersDisplay = document.createElement('div');
            filtersDisplay.className = 'active-filters';
            filtersDisplay.innerHTML = `
                <div class="filters-header">
                    <span><i class="fas fa-filter"></i> Active Filters:</span>
                    <button class="clear-all-filters" title="Clear all filters">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </div>
                <div class="filter-tags">
                    ${globalSearchTerm ? `<span class="filter-tag global-search">Global: "${globalSearchTerm}" <button onclick="clearGlobalSearch()">×</button></span>` : ''}
                    ${Object.entries(activeFilters).map(([colIndex, value]) => {
                        if (value) {
                            return `<span class="filter-tag">${headers[colIndex]}: "${value}" <button onclick="clearFilter(${colIndex})">×</button></span>`;
                        }
                        return '';
                    }).join('')}
                </div>
            `;
            
            const searchContainer = document.querySelector('.search-container');
            searchContainer.parentNode.insertBefore(filtersDisplay, searchContainer.nextSibling);
            
            // Add event listener for clear all button
            filtersDisplay.querySelector('.clear-all-filters').addEventListener('click', clearAllFilters);
        }
    }
    
    // Global functions for clearing filters
    window.clearFilter = function(columnIndex) {
        delete activeFilters[columnIndex];
        const filterSelect = document.querySelector(`#filter-${columnIndex}`);
        if (filterSelect) filterSelect.value = '';
        applyFilters();
    };
    
    window.clearGlobalSearch = function() {
        globalSearchTerm = '';
        const globalSearchInput = document.getElementById('table-search');
        if (globalSearchInput) globalSearchInput.value = '';
        applyFilters();
    };
    
    function clearAllFilters() {
        activeFilters = {};
        globalSearchTerm = '';
        
        // Clear all filter inputs
        document.querySelectorAll('.category-filter select').forEach(select => {
            select.value = '';
        });
        
        const globalSearchInput = document.getElementById('table-search');
        if (globalSearchInput) globalSearchInput.value = '';
        
        applyFilters();
    }
    
    // Add advanced search functionality
    const detailsSection = document.getElementById('data-toggle');
    if (detailsSection) {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container';
        
        // Create category filters
        const categoryFilters = headers.map((header, index) => {
        // Get unique values for this column
        const uniqueValues = [...new Set(allRows.map(row => {
            const cell = row.cells[index];
            return cell ? cell.textContent.trim() : '';
        }))].filter(value => value && value.length > 0).sort();
    
    const shouldShowFilter = (uniqueValues.length >= 2 && uniqueValues.length <= 50) || 
                           ['status', 'type', 'category', 'department', 'role', 'priority', 'level', 'grade'].some(keyword => 
                               header.toLowerCase().includes(keyword));
                            
        if (shouldShowFilter && uniqueValues.length > 0) {
            // Create a more readable label - avoid double pluralization
            const pluralLabel = header.toLowerCase().endsWith('s') ? 
                (header.toLowerCase() === 'users' ? 'Users' : header) : 
                `${header}s`;
            return `
                <div class="category-filter">
                    <label for="filter-${index}">${header}</label>
                    <select id="filter-${index}" data-column="${index}">
                        <option value="">All ${pluralLabel}</option>
                        ${uniqueValues.map(value => `<option value="${value}">${value.length > 30 ? value.substring(0, 27) + '...' : value}</option>`).join('')}
                    </select>
                </div>
            `;
        }
        return '';
    }).filter(filter => filter).join('');
        
        searchContainer.innerHTML = `
            <div class="search-controls">
                <div class="global-search">
                    <div class="search-box">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" id="table-search" placeholder="Search across all columns...">
                        <button id="clear-search" title="Clear search"><i class="fas fa-times"></i></button>
                    </div>
                </div>
                
                ${categoryFilters ? `
                    <div class="category-filters">
                        <div class="filters-toggle">
                            <button id="toggle-filters" class="toggle-btn">
                                <i class="fas fa-filter"></i> Advanced Filters
                                <i class="fas fa-chevron-down toggle-icon"></i>
                            </button>
                        </div>
                        <div class="filters-content" id="filters-content">
                            <div class="filters-grid">
                                ${categoryFilters}
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Insert search before pagination controls
        if (paginationControls) {
            paginationControls.parentNode.insertBefore(searchContainer, paginationControls);
        } else {
            detailsSection.insertBefore(searchContainer, dataTable.parentNode);
        }
        
        // Global search functionality
        const searchInput = document.getElementById('table-search');
        const clearButton = document.getElementById('clear-search');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                globalSearchTerm = e.target.value.trim();
                applyFilters();
                clearButton.style.display = globalSearchTerm ? 'block' : 'none';
            });
        }
        
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                globalSearchTerm = '';
                searchInput.value = '';
                applyFilters();
                clearButton.style.display = 'none';
                searchInput.focus();
            });
            clearButton.style.display = 'none';
        }
        
        // Category filters functionality
        document.querySelectorAll('.category-filter select').forEach(select => {
            select.addEventListener('change', (e) => {
                const columnIndex = parseInt(e.target.dataset.column);
                const filterValue = e.target.value;
                
                if (filterValue) {
                    activeFilters[columnIndex] = filterValue;
                } else {
                    delete activeFilters[columnIndex];
                }
                
                applyFilters();
            });
        });
        
        // Toggle filters visibility
        const toggleBtn = document.getElementById('toggle-filters');
        const filtersContent = document.getElementById('filters-content');
        const toggleIcon = toggleBtn?.querySelector('.toggle-icon');
        
        if (toggleBtn && filtersContent) {
            toggleBtn.addEventListener('click', () => {
                const isExpanded = filtersContent.classList.contains('expanded');
                
                if (isExpanded) {
                    filtersContent.classList.remove('expanded');
                    toggleIcon.style.transform = 'rotate(0deg)';
                } else {
                    filtersContent.classList.add('expanded');
                    toggleIcon.style.transform = 'rotate(180deg)';
                }
            });
        }
    }
});