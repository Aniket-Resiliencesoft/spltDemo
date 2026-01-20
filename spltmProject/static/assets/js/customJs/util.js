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
