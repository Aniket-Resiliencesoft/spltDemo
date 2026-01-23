/**
 * =========================================================
 * apiHelper.js
 * Centralized API + UI Helper
 * =========================================================
 */

/* ==============================
   ALERT & CONFIRM HELPERS
   ============================== */

/**
 * Show alert message
 * @param {boolean} success
 * @param {string} message
 */
function showAlert(success, message) {
    if (!message) return;

    if (success) {
        alert(`✅ ${message}`);
    } else {
        alert(`❌ ${message}`);
    }
}

/**
 * Show confirm dialog
 * @param {string} message
 * @returns {boolean}
 */
function showConfirm(message = "Are you sure?") {
    return confirm(message);
}

/* ==============================
   BASE RESPONSE HANDLER
   ============================== */

async function handleResponse(response) {
    const result = await response.json();

    const isSuccess = result.success ?? result.IsSuccess ?? result.is_success;
    if (!isSuccess) {
        showAlert(false, result.message || result.Message || "Operation failed");
        throw result;
    }

    return result;
}

/* ==============================
   AUTH HELPERS
   ============================== */

function getAuthToken() {
    const local = typeof localStorage !== 'undefined'
        ? localStorage.getItem('access_token')
        : null;
    if (local) return local;

    // fallback to cookie
    if (typeof document !== 'undefined' && document.cookie) {
        const match = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('access_token='));
        if (match) return decodeURIComponent(match.split('=')[1]);
    }
    return null;
}

function authHeaders(extra = {}) {
    const token = getAuthToken();
    const headers = { ...extra };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

/* ==============================
   GET APIs
   ============================== */

async function apiGet(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: authHeaders(),
        credentials: "same-origin",
    });
    return handleResponse(response);
}

async function apiGetById(url, id) {
    return apiGet(`${url}/${id}`);
}

async function apiGetList(url, params = {}) {
    const query = new URLSearchParams({
        pageNo: params.pageNo ?? 1,
        pageSize: params.pageSize ?? 10,
        fromDate: params.fromDate ?? "",
        toDate: params.toDate ?? "",
        status: params.status ?? ""
    }).toString();

    return apiGet(`${url}?${query}`);
}

/* ==============================
   POST APIs
   ============================== */

async function apiPost(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        credentials: "same-origin",
        body: JSON.stringify(data)
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

async function apiPostWithImage(url, formData) {
    const response = await fetch(url, {
        method: "POST",
        headers: authHeaders(),
        credentials: "same-origin",
        body: formData
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

/* ==============================
   PUT APIs
   ============================== */

async function apiPut(url, id, data) {
    const response = await fetch(`${url}/${id}`, {
        method: "PUT",
        headers: authHeaders({ "Content-Type": "application/json" }),
        credentials: "same-origin",
        body: JSON.stringify(data)
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

async function apiPutWithImage(url, id, formData) {
    const response = await fetch(`${url}/${id}`, {
        method: "PUT",
        headers: authHeaders(),
        credentials: "same-origin",
        body: formData
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

/* ==============================
   DELETE API (WITH CONFIRM)
   ============================== */

async function apiDelete(url, id, confirmMessage = "Are you sure you want to delete?") {
    if (!showConfirm(confirmMessage)) return null;

    const response = await fetch(`${url}/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
        credentials: "same-origin",
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

/* ==============================
   DROPDOWN BINDING
   ============================== */

function bindDropdown(elementId, data, defaultValue = null) {
    const ddl = document.getElementById(elementId);
    ddl.innerHTML = "";

    ddl.appendChild(new Option("-- Select --", ""));

    data.forEach(item => {
        const option = new Option(item.name, item.id);
        if (defaultValue && item.id == defaultValue) option.selected = true;
        ddl.appendChild(option);
    });
}

/* ==============================
   DATE CONVERSION
   ============================== */

function convertUtcToIndianTime(utcDate) {
    if (!utcDate) return "";

    return new Date(utcDate).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}
/* ==============================
   COMMON PAGINATION
   ============================== */

/**
 * Render pagination controls
 * @param {string} paginationElementId - ID of the pagination element
 * @param {number} currentPage - Current page number
 * @param {number} totalPages - Total number of pages
 * @param {function} onPageChange - Callback function when page is clicked
 */
function renderPagination(paginationElementId, currentPage, totalPages, onPageChange) {
    const paginationEl = document.getElementById(paginationElementId);
    if (!paginationEl) return;

    paginationEl.innerHTML = '';

    // Previous button
    const prevItem = document.createElement('li');
    prevItem.className = `page-item ${currentPage <= 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.innerText = 'Previous';
    prevLink.onclick = (e) => {
        e.preventDefault();
        if (currentPage > 1 && onPageChange) onPageChange(currentPage - 1);
    };
    prevItem.appendChild(prevLink);
    paginationEl.appendChild(prevItem);

    // Page numbers
    const maxPages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPages, startPage + maxPages - 1);

    if (endPage - startPage < maxPages - 1) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }

    if (startPage > 1) {
        const firstItem = document.createElement('li');
        firstItem.className = 'page-item';
        const firstLink = document.createElement('a');
        firstLink.className = 'page-link';
        firstLink.href = '#';
        firstLink.innerText = '1';
        firstLink.onclick = (e) => { e.preventDefault(); if (onPageChange) onPageChange(1); };
        firstItem.appendChild(firstLink);
        paginationEl.appendChild(firstItem);

        if (startPage > 2) {
            const ellipsis = document.createElement('li');
            ellipsis.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.innerText = '...';
            ellipsis.appendChild(ellipsisLink);
            paginationEl.appendChild(ellipsis);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const item = document.createElement('li');
        item.className = `page-item ${i === currentPage ? 'active' : ''}`;
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.innerText = i;
        link.onclick = (e) => {
            e.preventDefault();
            if (onPageChange) onPageChange(i);
        };
        item.appendChild(link);
        paginationEl.appendChild(item);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('li');
            ellipsis.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.innerText = '...';
            ellipsis.appendChild(ellipsisLink);
            paginationEl.appendChild(ellipsis);
        }

        const lastItem = document.createElement('li');
        lastItem.className = 'page-item';
        const lastLink = document.createElement('a');
        lastLink.className = 'page-link';
        lastLink.href = '#';
        lastLink.innerText = totalPages;
        lastLink.onclick = (e) => { e.preventDefault(); if (onPageChange) onPageChange(totalPages); };
        lastItem.appendChild(lastLink);
        paginationEl.appendChild(lastItem);
    }

    // Next button
    const nextItem = document.createElement('li');
    nextItem.className = `page-item ${currentPage >= totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.innerText = 'Next';
    nextLink.onclick = (e) => {
        e.preventDefault();
        if (currentPage < totalPages && onPageChange) onPageChange(currentPage + 1);
    };
    nextItem.appendChild(nextLink);
    paginationEl.appendChild(nextItem);
}

/**
 * Display pagination info (e.g., "Page 1 of 10")
 * @param {string} infoElementId - ID of the info element
 * @param {number} currentPage - Current page number
 * @param {number} totalPages - Total number of pages
 * @param {number} totalRecords - Total number of records
 */
function displayPaginationInfo(infoElementId, currentPage, totalPages, totalRecords) {
    const infoEl = document.getElementById(infoElementId);
    if (!infoEl) return;
    infoEl.innerHTML = `Page <strong>${currentPage}</strong> of <strong>${totalPages}</strong> (Total: <strong>${totalRecords}</strong> records)`;
}
