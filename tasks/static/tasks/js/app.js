/**
 * CHRONOTASK — SMART TASK BOARD APPLICATION JS
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    let tasks = [];
    let currentFilter = 'ALL';
    let currentPriority = 'ALL';
    let currentSort = 'NEWEST';
    let searchQuery = '';
    let tickerInterval = null;
    let currentCrypticTaskId = null;
    let typingTimer = null;

    // --- DOM Elements ---
    const taskGrid = document.getElementById('task-grid');
    const emptyState = document.getElementById('empty-state');
    
    // Stats Elements
    const valTotal = document.getElementById('val-total');
    const valActive = document.getElementById('val-active');
    const valLocked = document.getElementById('val-locked');
    const valEstTime = document.getElementById('val-est-time');

    // Controls
    const searchInput = document.getElementById('search-input');
    const filterTabs = document.querySelectorAll('.tab-btn');
    const priorityFilter = document.getElementById('priority-filter');
    const sortSelect = document.getElementById('sort-select');

    // Modals
    const createModal = document.getElementById('create-modal');
    const btnOpenCreateModal = document.getElementById('btn-open-create-modal');
    const btnCloseCreate = document.getElementById('btn-close-create');
    const btnCancelCreate = document.getElementById('btn-cancel-create');
    const createTaskForm = document.getElementById('create-task-form');

    const lockTypeSelect = document.getElementById('task-lock-type');
    const lockCountdownFields = document.getElementById('lock-countdown-fields');
    const lockCodeFields = document.getElementById('lock-code-fields');

    const btnRandomHint = document.getElementById('btn-random-hint');
    const taskHintInput = document.getElementById('task-hint');

    const btnSeedDemo = document.getElementById('btn-seed-demo');

    // Cryptic Modal
    const crypticModal = document.getElementById('cryptic-modal');
    const btnCloseCryptic = document.getElementById('btn-close-cryptic');
    const crypticTextEl = document.getElementById('cryptic-text');
    const crypticCountdownBox = document.getElementById('cryptic-countdown-box');
    const crypticTimerVal = document.getElementById('cryptic-timer-val');
    const crypticPasscodeBox = document.getElementById('cryptic-passcode-box');
    const passcodeAttemptInput = document.getElementById('passcode-attempt-input');
    const btnSubmitPasscode = document.getElementById('btn-submit-passcode');
    const passcodeError = document.getElementById('passcode-error');

    // Preset Cryptic Hints
    const PRESET_HINTS = [
        "Patience is a key written in shadow. The clock must speak '00:00' before the seal dissolves.",
        "The stars have not aligned. Wait for the celestial hands of time to turn.",
        "Shadows cannot step into the light before high noon.",
        "A secret phrase rests in the void. Speak the lost word to shatter the seal.",
        "The ancient hourglass still drips with sand. Do not rush destiny.",
        "The threshold remains closed to those who rush. Time itself holds the key.",
        "Echoes of incomplete time whisper: 'Not yet...'"
    ];

    // --- Initialization ---
    init();

    function init() {
        bindEvents();
        fetchTasks();
        startTicker();
    }

    // --- Event Listeners ---
    function bindEvents() {
        // Search & Filters
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderGrid();
        });

        filterTabs.forEach(btn => {
            btn.addEventListener('click', () => {
                filterTabs.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderGrid();
            });
        });

        priorityFilter.addEventListener('change', (e) => {
            currentPriority = e.target.value;
            renderGrid();
        });

        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            renderGrid();
        });

        // Create Modal Toggle
        btnOpenCreateModal.addEventListener('click', () => {
            createModal.classList.remove('hidden');
        });

        const closeCreateModal = () => {
            createModal.classList.add('hidden');
            createTaskForm.reset();
            lockCountdownFields.classList.add('hidden');
            lockCodeFields.classList.add('hidden');
        };

        btnCloseCreate.addEventListener('click', closeCreateModal);
        btnCancelCreate.addEventListener('click', closeCreateModal);

        lockTypeSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            lockCountdownFields.classList.toggle('hidden', val !== 'COUNTDOWN');
            lockCodeFields.classList.toggle('hidden', val !== 'CODE');
        });

        btnRandomHint.addEventListener('click', () => {
            const hint = PRESET_HINTS[Math.floor(Math.random() * PRESET_HINTS.length)];
            taskHintInput.value = hint;
        });

        createTaskForm.addEventListener('submit', handleCreateTask);
        btnSeedDemo.addEventListener('click', handleSeedDemo);

        // Cryptic Modal Events
        btnCloseCryptic.addEventListener('click', () => {
            crypticModal.classList.add('hidden');
            if (typingTimer) clearInterval(typingTimer);
        });

        btnSubmitPasscode.addEventListener('click', () => {
            const passcode = passcodeAttemptInput.value.trim();
            if (passcode && currentCrypticTaskId) {
                attemptCompleteTask(currentCrypticTaskId, passcode);
            }
        });

        passcodeAttemptInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                btnSubmitPasscode.click();
            }
        });
    }

    // --- API Calls ---
    async function fetchTasks() {
        try {
            const res = await fetch('/api/tasks/');
            const data = await res.json();
            if (data.success) {
                tasks = data.tasks;
                updateStats();
                renderGrid();
            }
        } catch (err) {
            console.error("Error fetching tasks:", err);
        }
    }

    async function handleCreateTask(e) {
        e.preventDefault();
        const title = document.getElementById('task-title').value.trim();
        const description = document.getElementById('task-desc').value.trim();
        const priority = document.getElementById('task-priority').value;
        const estimated_minutes = parseInt(document.getElementById('task-est').value) || 30;
        const lock_type = document.getElementById('task-lock-type').value;
        const countdown_minutes = parseInt(document.getElementById('task-countdown').value) || 5;
        const unlock_code = document.getElementById('task-code').value.trim();
        const cryptic_hint = document.getElementById('task-hint').value.trim();

        const payload = {
            title,
            description,
            priority,
            estimated_minutes,
            lock_type,
            countdown_minutes,
            unlock_code,
            cryptic_hint
        };

        try {
            const res = await fetch('/api/tasks/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                createModal.classList.add('hidden');
                createTaskForm.reset();
                lockCountdownFields.classList.add('hidden');
                lockCodeFields.classList.add('hidden');
                await fetchTasks();
            } else {
                alert(data.error || "Failed to create task.");
            }
        } catch (err) {
            console.error("Error creating task:", err);
        }
    }

    async function handleSeedDemo() {
        btnSeedDemo.disabled = true;
        btnSeedDemo.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Seeding...';
        try {
            const res = await fetch('/api/tasks/seed/', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                await fetchTasks();
            }
        } catch (err) {
            console.error("Error seeding tasks:", err);
        } finally {
            btnSeedDemo.disabled = false;
            btnSeedDemo.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Load Demo';
        }
    }

    async function attemptCompleteTask(taskId, passcode = '') {
        currentCrypticTaskId = taskId;
        try {
            const res = await fetch(`/api/tasks/${taskId}/complete/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ passcode })
            });

            const data = await res.json();

            if (res.ok && data.success) {
                // Success completion
                crypticModal.classList.add('hidden');
                await fetchTasks();
            } else {
                // Failed - Cryptic Hint Triggered!
                showCrypticHintModal(data, taskId);
            }
        } catch (err) {
            console.error("Error completing task:", err);
        }
    }

    async function deleteTask(taskId) {
        if (!confirm("Are you sure you want to delete this task?")) return;
        try {
            const res = await fetch(`/api/tasks/${taskId}/delete/`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                await fetchTasks();
            }
        } catch (err) {
            console.error("Error deleting task:", err);
        }
    }

    // --- UI Render Methods ---
    function updateStats() {
        const total = tasks.length;
        const active = tasks.filter(t => t.status !== 'COMPLETED' && !t.is_locked).length;
        const locked = tasks.filter(t => t.is_locked).length;
        const totalMinutes = tasks.reduce((sum, t) => sum + (t.status !== 'COMPLETED' ? t.estimated_minutes : 0), 0);

        valTotal.textContent = total;
        valActive.textContent = active;
        valLocked.textContent = locked;

        const hours = Math.floor(totalMinutes / 60);
        const mins = totalMinutes % 60;
        valEstTime.textContent = `${hours}h ${mins}m`;
    }

    function renderGrid() {
        let filtered = [...tasks];

        // Search
        if (searchQuery) {
            filtered = filtered.filter(t => 
                t.title.toLowerCase().includes(searchQuery) || 
                (t.description && t.description.toLowerCase().includes(searchQuery))
            );
        }

        // Status Filter
        if (currentFilter === 'PENDING') {
            filtered = filtered.filter(t => t.status === 'PENDING' && !t.is_locked);
        } else if (currentFilter === 'LOCKED') {
            filtered = filtered.filter(t => t.is_locked);
        } else if (currentFilter === 'COMPLETED') {
            filtered = filtered.filter(t => t.status === 'COMPLETED');
        }

        // Priority Filter
        if (currentPriority !== 'ALL') {
            filtered = filtered.filter(t => t.priority === currentPriority);
        }

        // Sorting
        if (currentSort === 'PRIORITY') {
            const order = { 'URGENT': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
            filtered.sort((a, b) => order[b.priority] - order[a.priority]);
        } else if (currentSort === 'ESTIMATED') {
            filtered.sort((a, b) => b.estimated_minutes - a.estimated_minutes);
        } else {
            // NEWEST
            filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        }

        if (filtered.length === 0) {
            taskGrid.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        taskGrid.innerHTML = filtered.map(t => createTaskCardHTML(t)).join('');

        // Attach action handlers
        filtered.forEach(t => {
            const btnComplete = document.getElementById(`btn-complete-${t.id}`);
            if (btnComplete) {
                btnComplete.addEventListener('click', () => attemptCompleteTask(t.id));
            }
            const btnDel = document.getElementById(`btn-del-${t.id}`);
            if (btnDel) {
                btnDel.addEventListener('click', () => deleteTask(t.id));
            }
        });
    }

    function createTaskCardHTML(task) {
        const isCompleted = task.status === 'COMPLETED';
        const isLocked = task.is_locked;

        let statusBadge = '';
        if (isCompleted) {
            statusBadge = `<span class="badge-status completed"><i class="fa-solid fa-circle-check"></i> Completed</span>`;
        } else if (isLocked) {
            statusBadge = `<span class="badge-status locked"><i class="fa-solid fa-lock"></i> Locked</span>`;
        } else {
            statusBadge = `<span class="badge-status ready"><i class="fa-solid fa-bolt"></i> Ready</span>`;
        }

        const priorityClass = task.priority.toLowerCase();
        const relativeTime = getRelativeTimeString(new Date(task.created_at));

        let countdownSection = '';
        if (isLocked && task.lock_type === 'COUNTDOWN') {
            const timeStr = formatCountdownString(task.remaining_seconds);
            countdownSection = `
                <div class="countdown-box" id="countdown-box-${task.id}">
                    <div class="countdown-label"><i class="fa-solid fa-clock text-accent"></i> Time Seal Countdown</div>
                    <div class="countdown-clock" id="clock-${task.id}">${timeStr}</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="pbar-${task.id}"></div>
                    </div>
                </div>
            `;
        } else if (isLocked && task.lock_type === 'CODE') {
            countdownSection = `
                <div class="countdown-box" style="border-color: rgba(6, 182, 212, 0.3);">
                    <div class="countdown-label"><i class="fa-solid fa-key text-accent"></i> Passcode Protected</div>
                    <div class="countdown-clock" style="font-size: 1rem; color: #06b6d4;">SECRET PASSPHRASE SEALED</div>
                </div>
            `;
        }

        let actionBtnText = '<i class="fa-solid fa-check"></i> Complete';
        let actionBtnClass = 'btn-primary';
        if (isCompleted) {
            actionBtnText = '<i class="fa-solid fa-check-double"></i> Finished';
            actionBtnClass = 'btn-secondary';
        } else if (isLocked) {
            actionBtnText = '<i class="fa-solid fa-lock-open"></i> Attempt Unlock';
            actionBtnClass = 'btn-accent';
        }

        return `
            <div class="task-card ${isLocked ? 'is-locked' : ''} ${isCompleted ? 'is-completed' : ''}" id="task-card-${task.id}">
                <div>
                    <div class="card-top">
                        <span class="badge-priority ${priorityClass}">${task.priority}</span>
                        ${statusBadge}
                    </div>
                    <h3 class="task-title">${escapeHTML(task.title)}</h3>
                    <p class="task-desc">${escapeHTML(task.description || 'No description provided.')}</p>
                </div>

                <div>
                    ${countdownSection}

                    <div class="task-meta">
                        <span class="meta-item"><i class="fa-regular fa-clock"></i> ${task.estimated_minutes} mins</span>
                        <span class="meta-item"><i class="fa-regular fa-calendar"></i> ${relativeTime}</span>
                    </div>

                    <div class="card-actions">
                        <button id="btn-complete-${task.id}" class="btn ${actionBtnClass} btn-complete" ${isCompleted ? 'disabled' : ''}>
                            ${actionBtnText}
                        </button>
                        <button id="btn-del-${task.id}" class="btn btn-delete" title="Delete Task">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // --- Cryptic Modal & Typing Effect ---
    function showCrypticHintModal(data, taskId) {
        crypticModal.classList.remove('hidden');
        passcodeError.classList.add('hidden');
        passcodeAttemptInput.value = '';

        const hintText = data.cryptic_hint || "The seal remains unbroken. Time flows relentless.";

        // Typewriter Effect
        typeWriter(hintText, crypticTextEl);

        // Show passcode box if required
        if (data.reason === 'locked_code' || data.requires_passcode) {
            crypticPasscodeBox.classList.remove('hidden');
            passcodeAttemptInput.focus();
        } else {
            crypticPasscodeBox.classList.add('hidden');
        }

        // Show countdown if countdown locked
        if (data.reason === 'locked_time' && data.remaining_seconds > 0) {
            crypticCountdownBox.classList.remove('hidden');
            crypticTimerVal.textContent = formatCountdownString(data.remaining_seconds);
        } else {
            crypticCountdownBox.classList.add('hidden');
        }
    }

    function typeWriter(text, element) {
        if (typingTimer) clearInterval(typingTimer);
        element.textContent = '';
        let i = 0;
        typingTimer = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typingTimer);
            }
        }, 30);
    }

    // --- Ticker for Countdown Timers ---
    function startTicker() {
        if (tickerInterval) clearInterval(tickerInterval);
        tickerInterval = setInterval(() => {
            let needReRender = false;
            tasks.forEach(t => {
                if (t.is_locked && t.lock_type === 'COUNTDOWN' && t.remaining_seconds > 0) {
                    t.remaining_seconds -= 1;
                    const clockEl = document.getElementById(`clock-${t.id}`);
                    if (clockEl) {
                        clockEl.textContent = formatCountdownString(t.remaining_seconds);
                    }
                    if (t.remaining_seconds <= 0) {
                        t.is_locked = false;
                        needReRender = true;
                    }
                }
            });
            if (needReRender) {
                updateStats();
                renderGrid();
            }
        }, 1000);
    }

    // --- Utility Helpers ---
    function formatCountdownString(totalSecs) {
        const secs = Math.max(0, totalSecs);
        const mins = Math.floor(secs / 60);
        const remSecs = secs % 60;
        return `${String(mins).padStart(2, '0')}:${String(remSecs).padStart(2, '0')}`;
    }

    function getRelativeTimeString(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
});
