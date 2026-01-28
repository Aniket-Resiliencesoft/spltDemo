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

    if (!result.success) {
        showAlert(false, result.message || "Operation failed");
        throw result;
    }

    return result;
}

/* ==============================
   GET APIs
   ============================== */

async function apiGet(url) {
    const response = await fetch(url, { method: "GET" });
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

async function apiPostWithImage(url, formData) {
    const response = await fetch(url, {
        method: "POST",
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await handleResponse(response);
    showAlert(true, result.message);
    return result;
}

async function apiPutWithImage(url, id, formData) {
    const response = await fetch(`${url}/${id}`, {
        method: "PUT",
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
        method: "DELETE"
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
    const container = document.getElementById(paginationElementId);
    if (!container) return;
 
    container.innerHTML = '';
 
    const maxVisible = 5;
 
    /* ---------- PREVIOUS ---------- */
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pg-btn';
    prevBtn.innerHTML = '‹ Previous';
 
    if (currentPage === 1) {
        prevBtn.classList.add('disabled');
    } else {
        prevBtn.onclick = () => onPageChange(currentPage - 1);
    }
 
    container.appendChild(prevBtn);
 
    /* ---------- PAGE NUMBERS ---------- */
    const pagesWrap = document.createElement('div');
    pagesWrap.className = 'pg-pages';
 
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
 
    if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1);
    }
 
    // First page
    if (start > 1) {
        pagesWrap.appendChild(createPageBtn(1, currentPage, onPageChange));
 
        if (start > 2) {
            pagesWrap.appendChild(createEllipsis());
        }
    }
 
    // Middle pages
    for (let i = start; i <= end; i++) {
        pagesWrap.appendChild(createPageBtn(i, currentPage, onPageChange));
    }
 
    // Last page
    if (end < totalPages) {
        if (end < totalPages - 1) {
            pagesWrap.appendChild(createEllipsis());
        }
 
        pagesWrap.appendChild(createPageBtn(totalPages, currentPage, onPageChange));
    }
 
    container.appendChild(pagesWrap);
 
    /* ---------- NEXT ---------- */
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pg-btn';
    nextBtn.innerHTML = 'Next ›';
 
    if (currentPage === totalPages) {
        nextBtn.classList.add('disabled');
    } else {
        nextBtn.onclick = () => onPageChange(currentPage + 1);
    }
 
    container.appendChild(nextBtn);
}
 
/* ---------- HELPERS ---------- */
 
function createPageBtn(page, currentPage, onPageChange) {
    const btn = document.createElement('button');
    btn.className = 'pg-page';
    btn.innerText = page;
 
    if (page === currentPage) {
        btn.classList.add('active');
    } else {
        btn.onclick = () => onPageChange(page);
    }
 
    return btn;
}
 
function createEllipsis() {
    const span = document.createElement('span');
    span.className = 'pg-ellipsis';
    span.innerText = '…';
    return span;
}
 
/**
 * Display pagination info (e.g., "Page 1 of 10")
 * @param {string} infoElementId - ID of the info element
 * @param {number} currentPage - Current page number
 * @param {number} totalPages - Total number of pages
 * @param {number} totalRecords - Total number of records
 */
// function displayPaginationInfo(infoElementId, currentPage, totalPages, totalRecords) {
//     const infoEl = document.getElementById(infoElementId);
//     if (!infoEl) return;
//     infoEl.innerHTML = `Page <strong>${currentPage}</strong> of <strong>${totalPages}</strong> (Total: <strong>${totalRecords}</strong> records)`;
// }
 
function displayPaginationInfo(infoElementId, currentPage, totalPages, totalRecords) {
    const infoEl = document.getElementById(infoElementId);
    if (!infoEl) return;
 
    const from = (currentPage - 1) * 10 + 1;
    const to = Math.min(currentPage * 10, totalRecords);
 
    infoEl.innerHTML = `Showing <strong>${from}-${to}</strong> of <strong>${totalRecords}</strong> results`;
}