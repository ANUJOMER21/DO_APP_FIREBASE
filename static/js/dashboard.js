// Global variables
let allDevices = {};
let selectedDevices = new Set();

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDevices();
    loadStats();
    
    // Set up auto-refresh every 10 seconds
    setInterval(() => {
        loadDevices();
        loadStats();
    }, 10000);
    
    // Set up APK upload form
    document.getElementById('apkUploadForm').addEventListener('submit', uploadAPK);
});

// Load all devices
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        if (data.success) {
            allDevices = data.devices || {};
            renderDevicesTable();
        } else {
            showToast('Error loading devices: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error loading devices:', error);
        showToast('Failed to load devices', 'error');
    }
}

// Render devices table
function renderDevicesTable() {
    const tbody = document.getElementById('devicesTableBody');
    
    if (Object.keys(allDevices).length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No devices registered yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    Object.entries(allDevices).forEach(([deviceId, deviceInfo]) => {
        const row = document.createElement('tr');
        const status = deviceInfo.status || 'offline';
        const lastUpdated = deviceInfo.lastUpdated || 'Never';
        
        row.innerHTML = `
            <td>
                <input type="checkbox" class="device-checkbox" value="${deviceId}" 
                       onchange="updateSelectedDevices('${deviceId}', this.checked)">
            </td>
            <td><code>${deviceId}</code></td>
            <td>
                <span class="status-badge status-${status}">
                    <i class="fas fa-circle"></i> ${status.toUpperCase()}
                </span>
            </td>
            <td>${lastUpdated}</td>
            <td>
                <button class="btn btn-sm btn-danger btn-action" onclick="sendCommand('${deviceId}', 'lock')">
                    <i class="fas fa-lock"></i> Lock
                </button>
                <button class="btn btn-sm btn-success btn-action" onclick="sendCommand('${deviceId}', 'unlock')">
                    <i class="fas fa-unlock"></i> Unlock
                </button>
                <button class="btn btn-sm btn-info btn-action" onclick="promptWallpaper('${deviceId}')">
                    <i class="fas fa-image"></i> Wallpaper
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Filter devices
function filterDevices() {
    const searchTerm = document.getElementById('searchDevices').value.toLowerCase();
    const rows = document.querySelectorAll('#devicesTableBody tr');
    
    rows.forEach(row => {
        const deviceId = row.querySelector('code')?.textContent.toLowerCase() || '';
        if (deviceId.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Update selected devices
function updateSelectedDevices(deviceId, isSelected) {
    if (isSelected) {
        selectedDevices.add(deviceId);
    } else {
        selectedDevices.delete(deviceId);
    }
    updateSelectAllCheckbox();
}

// Toggle select all
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll').checked;
    const checkboxes = document.querySelectorAll('.device-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll;
        updateSelectedDevices(checkbox.value, selectAll);
    });
}

// Update select all checkbox state
function updateSelectAllCheckbox() {
    const checkboxes = document.querySelectorAll('.device-checkbox');
    const checkedCount = document.querySelectorAll('.device-checkbox:checked').length;
    document.getElementById('selectAll').checked = checkedCount === checkboxes.length && checkboxes.length > 0;
}

// Send command to a single device
async function sendCommand(deviceId, command) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Command "${command}" sent to device ${deviceId}`, 'success');
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error sending command:', error);
        showToast('Failed to send command', 'error');
    }
}

// Prompt for wallpaper URL
function promptWallpaper(deviceId) {
    const url = prompt('Enter wallpaper image URL:');
    if (url && url.trim()) {
        sendCommand(deviceId, `wallpaper:${url.trim()}`);
    }
}

// Send bulk command
async function sendBulkCommand() {
    if (selectedDevices.size === 0) {
        showToast('Please select at least one device', 'warning');
        return;
    }
    
    let command = document.getElementById('bulkCommand').value;
    const wallpaperUrl = document.getElementById('wallpaperUrl').value.trim();
    
    if (wallpaperUrl) {
        command = `wallpaper:${wallpaperUrl}`;
    }
    
    try {
        const response = await fetch('/api/devices/bulk-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_ids: Array.from(selectedDevices),
                command: command
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const successCount = data.results.filter(r => r.success).length;
            showToast(`Command sent to ${successCount} out of ${data.results.length} devices`, 'success');
            
            // Clear wallpaper URL input
            if (wallpaperUrl) {
                document.getElementById('wallpaperUrl').value = '';
            }
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error sending bulk command:', error);
        showToast('Failed to send bulk command', 'error');
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('totalCount').textContent = stats.total_devices;
            document.getElementById('onlineCount').textContent = stats.online_devices;
            document.getElementById('offlineCount').textContent = stats.offline_devices;
            document.getElementById('totalDevices').textContent = `${stats.total_devices} Devices`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Upload APK
async function uploadAPK(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('apkFile');
    const checksumInput = document.getElementById('apkChecksum');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select an APK file', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('apk', file);
    
    // Add checksum if provided
    const checksum = checksumInput.value.trim();
    if (checksum) {
        formData.append('checksum', checksum);
    }
    
    try {
        showToast('Uploading APK...', 'info');
        
        const response = await fetch('/api/apk/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = data.checksum_provided 
                ? 'APK uploaded successfully with checksum!'
                : 'APK uploaded successfully!';
            showToast(message, 'success');
            fileInput.value = '';
            checksumInput.value = '';
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error uploading APK:', error);
        showToast('Failed to upload APK', 'error');
    }
}

// Show Device Owner QR code
async function showQRCode() {
    const modal = new bootstrap.Modal(document.getElementById('qrModal'));
    const container = document.getElementById('qrCodeContainer');
    const downloadLink = document.getElementById('downloadLink');
    
    container.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Generating QR Code...</span></div>';
    modal.show();
    
    try {
        // Use Device Owner provisioning QR endpoint
        const response = await fetch('/api/apk/device-owner-qr');
        const data = await response.json();
        
        if (data.success) {
            container.innerHTML = `<img src="${data.qr_code}" alt="QR Code">`;
            // Keep direct download link for convenience
            downloadLink.href = data.download_url;
            downloadLink.textContent = `Download ${data.apk_filename}`;
        } else {
            container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            downloadLink.style.display = 'none';
        }
    } catch (error) {
        console.error('Error generating QR code:', error);
        container.innerHTML = '<div class="alert alert-danger">Failed to generate QR code</div>';
        downloadLink.style.display = 'none';
    }
}

// Update checksum for latest APK
async function updateChecksum() {
    const checksumInput = document.getElementById('updateChecksum');
    const checksum = checksumInput.value.trim();
    
    if (!checksum) {
        showToast('Please enter a checksum', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/apk/set-checksum', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ checksum: checksum })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = data.checksum_normalized 
                ? `Checksum updated for ${data.filename}\nOriginal: ${data.checksum_original}\nNormalized: ${data.checksum_normalized}`
                : `Checksum updated for ${data.filename}`;
            showToast(message, 'success');
            checksumInput.value = '';
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error updating checksum:', error);
        showToast('Failed to update checksum', 'error');
    }
}

// View current checksum information
async function viewChecksum() {
    try {
        const response = await fetch('/api/apk/verify-checksum');
        const data = await response.json();
        
        if (data.success) {
            let message = `Checksum for: ${data.filename}\n\n`;
            message += `Computed (Base64URL): ${data.checksum_base64url}\n`;
            message += `Computed (Base64): ${data.checksum_base64}\n`;
            message += `Computed (Hex): ${data.checksum_hex}\n`;
            if (data.stored_checksum) {
                message += `\nStored Checksum: ${data.stored_checksum}`;
            } else {
                message += `\nNo stored checksum (using computed)`;
            }
            alert(message);
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error viewing checksum:', error);
        showToast('Failed to view checksum', 'error');
    }
}

// Refresh devices
function refreshDevices() {
    loadDevices();
    loadStats();
    showToast('Refreshing devices...', 'info');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toastBody');
    
    // Remove existing alert classes
    toast.classList.remove('bg-primary', 'bg-success', 'bg-danger', 'bg-warning');
    
    // Add appropriate class
    if (type === 'success') {
        toast.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toast.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning', 'text-dark');
    } else {
        toast.classList.add('bg-primary', 'text-white');
    }
    
    toastBody.textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

