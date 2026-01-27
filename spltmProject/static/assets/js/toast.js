/**
 * Toast Notification System
 * Displays beautiful toast notifications for user feedback
 */

function showToast(message, type = 'info', duration = 3000) {
  // Create toast container if it doesn't exist
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 10px;
      font-family: 'Inter', sans-serif;
    `;
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toast = document.createElement('div');
  const toastId = 'toast-' + Date.now();
  toast.id = toastId;

  // Define colors based on type
  const colors = {
    success: { bg: '#10b981', icon: '✓' },
    error: { bg: '#ef4444', icon: '✕' },
    warning: { bg: '#f59e0b', icon: '⚠' },
    info: { bg: '#3b82f6', icon: 'ℹ' }
  };

  const config = colors[type] || colors.info;

  toast.style.cssText = `
    background: ${config.bg};
    color: white;
    padding: 16px 24px;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 300px;
    max-width: 400px;
    animation: slideIn 0.3s ease;
    font-size: 14px;
    font-weight: 500;
  `;

  // Add icon
  const icon = document.createElement('span');
  icon.textContent = config.icon;
  icon.style.cssText = `
    font-size: 18px;
    font-weight: bold;
    min-width: 24px;
    text-align: center;
  `;

  // Add message
  const messageEl = document.createElement('span');
  messageEl.textContent = message;
  messageEl.style.cssText = `
    flex: 1;
    word-break: break-word;
  `;

  // Add close button
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '×';
  closeBtn.style.cssText = `
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    min-width: 24px;
    text-align: center;
    transition: opacity 0.2s ease;
  `;
  closeBtn.onmouseover = () => closeBtn.style.opacity = '0.7';
  closeBtn.onmouseout = () => closeBtn.style.opacity = '1';
  closeBtn.onclick = () => removeToast(toastId);

  toast.appendChild(icon);
  toast.appendChild(messageEl);
  toast.appendChild(closeBtn);

  toastContainer.appendChild(toast);

  // Auto remove after duration
  if (duration > 0) {
    setTimeout(() => removeToast(toastId), duration);
  }
}

function removeToast(toastId) {
  const toast = document.getElementById(toastId);
  if (toast) {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }
}

function showSuccessToast(message) {
  showToast(message, 'success', 3000);
}

function showErrorToast(message) {
  showToast(message, 'error', 4000);
}

function showWarningToast(message) {
  showToast(message, 'warning', 3500);
}

function showInfoToast(message) {
  showToast(message, 'info', 3000);
}

/**
 * Extract error message from API response
 * Handles validation errors and converts them to readable messages
 */
function getErrorMessage(xhr) {
  if (!xhr.responseJSON) {
    return 'An error occurred. Please try again.';
  }

  const response = xhr.responseJSON;

  // If Message field exists and is not "Validation failed", use it
  if (response.Message && response.Message !== 'Validation failed') {
    return response.Message;
  }

  // If there's validation error data, extract field errors
  if (response.Data && typeof response.Data === 'object') {
    const errors = [];
    for (let field in response.Data) {
      if (response.Data.hasOwnProperty(field)) {
        const fieldErrors = response.Data[field];
        if (Array.isArray(fieldErrors)) {
          errors.push(fieldErrors[0]); // Get first error message
        } else if (typeof fieldErrors === 'string') {
          errors.push(fieldErrors);
        }
      }
    }
    if (errors.length > 0) {
      return errors.join(' ');
    }
  }

  // Fallback to Message
  if (response.Message) {
    return response.Message;
  }

  return 'An error occurred. Please try again.';
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);
