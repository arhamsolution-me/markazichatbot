document.addEventListener("DOMContentLoaded", () => {
    const STORAGE_KEY_SESSIONS = "markazi_chat_sessions";
    const STORAGE_KEY_CURRENT = "markazi_current_session_id";

    const appRoot = document.getElementById("app-root");
    const chatViewport = document.getElementById("chat-viewport");
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const syncBtn = document.getElementById("sync-btn");
    const clearChatBtn = document.getElementById("clear-chat-btn");

    // History Drawer Elements
    const historyToggleBtn = document.getElementById("history-toggle-btn");
    const historyDrawer = document.getElementById("history-drawer");
    const historyBackdrop = document.getElementById("history-backdrop");
    const closeHistoryBtn = document.getElementById("close-history-btn");
    const historyList = document.getElementById("history-list");
    const drawerNewChatBtn = document.getElementById("drawer-new-chat-btn");
    const clearAllHistoryBtn = document.getElementById("clear-all-history-btn");

    let currentSessionId = null;
    let currentMessages = []; // Array of { role: 'user' | 'assistant', content: string }

    // --- Session Storage Utilities ---
    function getStoredSessions() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY_SESSIONS);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            console.error("Error reading sessions:", e);
            return [];
        }
    }

    function saveStoredSessions(sessions) {
        try {
            localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
        } catch (e) {
            console.error("Error saving sessions:", e);
        }
    }

    function saveCurrentSession() {
        if (!currentMessages.length) return;
        const sessions = getStoredSessions();
        const existingIndex = sessions.findIndex(s => s.id === currentSessionId);
        
        const firstUserMsg = currentMessages.find(m => m.role === "user");
        const title = firstUserMsg ? firstUserMsg.content.slice(0, 45) + (firstUserMsg.content.length > 45 ? "..." : "") : "New Conversation";

        const sessionData = {
            id: currentSessionId,
            title: title,
            timestamp: Date.now(),
            messages: currentMessages
        };

        if (existingIndex >= 0) {
            sessions[existingIndex] = sessionData;
        } else {
            sessions.unshift(sessionData);
        }

        saveStoredSessions(sessions);
        try {
            localStorage.setItem(STORAGE_KEY_CURRENT, currentSessionId);
        } catch (e) {}
        renderHistoryList();
    }

    function deleteSession(id, e) {
        if (e) e.stopPropagation();
        let sessions = getStoredSessions();
        sessions = sessions.filter(s => s.id !== id);
        saveStoredSessions(sessions);

        if (currentSessionId === id) {
            resetToLandingMode();
        } else {
            renderHistoryList();
        }
    }

    function clearAllHistory() {
        if (!confirm("Are you sure you want to delete all saved conversations?")) return;
        localStorage.removeItem(STORAGE_KEY_SESSIONS);
        localStorage.removeItem(STORAGE_KEY_CURRENT);
        resetToLandingMode();
        renderHistoryList();
    }

    function loadSession(session) {
        currentSessionId = session.id;
        currentMessages = [...session.messages];
        try {
            localStorage.setItem(STORAGE_KEY_CURRENT, currentSessionId);
        } catch (e) {}

        // Render in chat viewport
        chatMessages.innerHTML = "";
        for (const msg of currentMessages) {
            if (msg.role === "user") {
                appendUserMessageToDOM(msg.content);
            } else {
                appendAssistantMessageToDOM(msg.content);
            }
        }

        activateChatMode();
        closeDrawer();
        scrollToBottom();
        if (userInput) userInput.focus();
    }

    function renderHistoryList() {
        if (!historyList) return;
        const sessions = getStoredSessions();
        if (!sessions.length) {
            historyList.innerHTML = `<div class="history-empty">No saved conversations yet.</div>`;
            return;
        }

        historyList.innerHTML = "";
        for (const s of sessions) {
            const item = document.createElement("div");
            item.className = "history-item" + (s.id === currentSessionId ? " active" : "");
            
            const dateStr = formatTimestamp(s.timestamp);

            item.innerHTML = `
                <div class="history-item-info">
                    <div class="history-item-title" title="${escapeHtml(s.title)}">${escapeHtml(s.title)}</div>
                    <div class="history-item-date">${dateStr} · ${s.messages.length} messages</div>
                </div>
                <button class="history-item-del" title="Delete conversation">✕</button>
            `;

            item.addEventListener("click", () => loadSession(s));
            const delBtn = item.querySelector(".history-item-del");
            delBtn.addEventListener("click", (ev) => deleteSession(s.id, ev));

            historyList.appendChild(item);
        }
    }

    function formatTimestamp(ts) {
        if (!ts) return "";
        const date = new Date(ts);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        if (diffDays === 0) {
            return "Today, " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return "Yesterday, " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    }

    // --- Drawer Controls ---
    function openDrawer() {
        if (historyDrawer) historyDrawer.classList.add("open");
        if (historyBackdrop) historyBackdrop.classList.add("open");
        renderHistoryList();
    }

    function closeDrawer() {
        if (historyDrawer) historyDrawer.classList.remove("open");
        if (historyBackdrop) historyBackdrop.classList.remove("open");
    }

    if (historyToggleBtn) historyToggleBtn.addEventListener("click", openDrawer);
    if (closeHistoryBtn) closeHistoryBtn.addEventListener("click", closeDrawer);
    if (historyBackdrop) historyBackdrop.addEventListener("click", closeDrawer);
    if (clearAllHistoryBtn) clearAllHistoryBtn.addEventListener("click", clearAllHistory);
    if (drawerNewChatBtn) {
        drawerNewChatBtn.addEventListener("click", () => {
            closeDrawer();
            resetToLandingMode();
        });
    }

    // --- Workspace Mode Transitions ---
    function activateChatMode() {
        if (appRoot && appRoot.classList.contains("landing-mode")) {
            appRoot.classList.remove("landing-mode");
            appRoot.classList.add("active-mode");
        }
    }

    function resetToLandingMode() {
        currentSessionId = null;
        currentMessages = [];
        try {
            localStorage.removeItem(STORAGE_KEY_CURRENT);
        } catch (e) {}

        if (appRoot) {
            appRoot.classList.remove("active-mode");
            appRoot.classList.add("landing-mode");
        }
        if (chatMessages) {
            chatMessages.innerHTML = "";
        }
        if (userInput) {
            userInput.value = "";
            userInput.style.height = "auto";
            userInput.focus();
        }
        renderHistoryList();
    }

    if (clearChatBtn) clearChatBtn.addEventListener("click", resetToLandingMode);

    // Auto-resize textarea
    if (userInput) {
        userInput.addEventListener("input", function() {
            this.style.height = "auto";
            this.style.height = (this.scrollHeight) + "px";
        });

        userInput.addEventListener("keydown", function(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    }

    // Manual DB Sync
    if (syncBtn) {
        syncBtn.addEventListener("click", async () => {
            syncBtn.disabled = true;
            const originalText = syncBtn.innerHTML;
            syncBtn.innerHTML = `<span>Syncing...</span>`;
            try {
                const res = await fetch("/api/sync", { method: "POST" });
                const data = await res.json();
                alert("✓ " + (data.message || "Vector Catalog re-synchronized successfully!"));
            } catch (e) {
                alert("Sync failed: " + e.message);
            } finally {
                syncBtn.disabled = false;
                syncBtn.innerHTML = originalText;
            }
        });
    }

    // Chat Submission with Multi-turn History & Real-time SSE Streaming
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // Initialize session ID if starting fresh
        if (!currentSessionId) {
            currentSessionId = "sess_" + Date.now();
        }

        // Transition from centered landing to active chat
        activateChatMode();

        // Render User Message & record in history
        appendUserMessageToDOM(text);
        
        // Prepare context history (exclude current message)
        const historyPayload = [...currentMessages];
        
        // Append user turn to local history
        currentMessages.push({ role: "user", content: text });
        saveCurrentSession();

        userInput.value = "";
        userInput.style.height = "auto";
        sendBtn.disabled = true;

        // Create Streaming Assistant Bubble
        const streamBubble = createStreamingBubble();
        scrollToBottom();

        let accumulatedText = "";
        let metaData = null;

        try {
            const response = await fetch("/api/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    history: historyPayload
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: "Unknown server error" }));
                streamBubble.setError(errData.detail || "Error connecting to AI service.");
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            let hasError = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const parts = buffer.split("\n\n");
                buffer = parts.pop(); // keep incomplete chunk

                for (const part of parts) {
                    if (!part.trim()) continue;
                    const eventMatch = part.match(/event:\s*([a-zA-Z0-9_-]+)/);
                    const dataMatch = part.match(/data:\s*([\s\S]+)/);
                    if (!dataMatch) continue;

                    const event = eventMatch ? eventMatch[1] : "token";
                    let payload;
                    try {
                        payload = JSON.parse(dataMatch[1]);
                    } catch (e) {
                        continue;
                    }

                    if (event === "stage") {
                        streamBubble.setStage(payload.message);
                    } else if (event === "token") {
                        accumulatedText += payload.token;
                        streamBubble.appendContent(accumulatedText);
                        scrollToBottom();
                    } else if (event === "done") {
                        metaData = payload;
                    } else if (event === "error") {
                        hasError = true;
                        streamBubble.setError(payload.error || "An error occurred.");
                    }
                }
            }

            if (!hasError || (accumulatedText && accumulatedText.trim())) {
                streamBubble.finalize(accumulatedText, metaData);
            }

            // Record turn in history with executed SQL for multi-turn follow-ups
            if (accumulatedText && accumulatedText.trim()) {
                currentMessages.push({
                    role: "assistant",
                    content: accumulatedText,
                    sql: metaData ? metaData.sql : null
                });
                saveCurrentSession();
            }

        } catch (err) {
            streamBubble.setError("Connection failed: " + err.message);
        } finally {
            sendBtn.disabled = false;
            scrollToBottom();
            if (userInput) userInput.focus();
        }
    });

    // --- DOM Append & Streaming Utilities ---
    function appendUserMessageToDOM(text) {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper user-wrapper";
        wrapper.innerHTML = `
            <div class="avatar user-avatar">U</div>
            <div class="message-body">
                <div class="message-bubble user-bubble">
                    <p>${escapeHtml(text)}</p>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
    }

    function createStreamingBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper assistant-wrapper";
        wrapper.innerHTML = `
            <div class="avatar assistant-avatar">✦</div>
            <div class="message-body">
                <div class="stage-pill" id="bubble-stage-pill">
                    <span class="status-dot"></span>
                    <span id="bubble-stage-text">Connecting...</span>
                </div>
                <div class="message-bubble assistant-bubble">
                    <div class="bubble-content"></div>
                    <div class="bubble-chart-slot"></div>
                    <div class="bubble-actions-slot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);

        const stagePill = wrapper.querySelector("#bubble-stage-pill");
        const stageText = wrapper.querySelector("#bubble-stage-text");
        const contentDiv = wrapper.querySelector(".bubble-content");
        const chartSlot = wrapper.querySelector(".bubble-chart-slot");
        const actionsSlot = wrapper.querySelector(".bubble-actions-slot");

        return {
            setStage: (msg) => {
                if (stageText) stageText.textContent = msg;
            },
            appendContent: (fullText) => {
                if (stagePill && stagePill.style.display !== "none") {
                    stagePill.style.display = "none";
                }
                contentDiv.innerHTML = formatMarkdown(fullText);
            },
            setError: (errMsg) => {
                if (stagePill) stagePill.remove();
                contentDiv.innerHTML = `
                    <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 8px; padding: 10px 14px; margin: 4px 0;">
                        <p style="color: #f43f5e; margin: 0 0 4px 0; font-weight: 600; font-size: 0.9em;">⚠️ System Notice:</p>
                        <p style="color: #fecdd3; margin: 0; font-size: 0.88em; line-height: 1.4;">${escapeHtml(errMsg)}</p>
                    </div>
                `;
            },
            finalize: (fullText, meta) => {
                if (stagePill) stagePill.remove();
                if (fullText && fullText.trim()) {
                    contentDiv.innerHTML = formatMarkdown(fullText);
                } else if (!contentDiv.innerHTML || !contentDiv.textContent.trim()) {
                    contentDiv.innerHTML = `
                        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px 14px; margin: 4px 0;">
                            <p style="color: #f59e0b; margin: 0; font-size: 0.9em;">⚠️ Server se koi jawab receive nahi hua. Barah-e-karam apna sawal dobara bhejien.</p>
                        </div>
                    `;
                }

                if (meta) {
                    // Render Chart if chart data exists
                    if (meta.chart) {
                        renderChart(chartSlot, meta.chart);
                    }

                    // Render Actions Toolbar (Download CSV + View SQL)
                    if ((meta.rows && meta.rows.length) || meta.sql) {
                        renderActionsToolbar(actionsSlot, meta);
                    }
                }
            }
        };
    }

    function renderChart(container, chartData) {
        if (!chartData || typeof Chart === "undefined") return;
        const card = document.createElement("div");
        card.className = "chart-card";
        card.innerHTML = `
            <div class="chart-header">
                <span class="chart-title">📊 ${escapeHtml(chartData.title || 'Analytics')}</span>
            </div>
            <div class="chart-canvas-container">
                <canvas></canvas>
            </div>
        `;
        container.appendChild(card);
        const canvas = card.querySelector("canvas");

        const palette = [
            '#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899',
            '#8b5cf6', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
        ];

        new Chart(canvas, {
            type: chartData.type || 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: chartData.value_name ? chartData.value_name.replace(/_/g, ' ').toUpperCase() : 'VALUE',
                    data: chartData.data,
                    backgroundColor: chartData.type === 'doughnut' ? palette : 'rgba(99, 102, 241, 0.85)',
                    borderColor: '#4f46e5',
                    borderWidth: chartData.type === 'doughnut' ? 0 : 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: chartData.type === 'doughnut' }
                },
                scales: chartData.type === 'doughnut' ? {} : {
                    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function renderActionsToolbar(container, meta) {
        const toolbar = document.createElement("div");
        toolbar.className = "data-actions-toolbar";
        
        const rowCount = meta.row_count || (meta.rows ? meta.rows.length : 0);
        let html = `
            <div class="toolbar-btn-group">
        `;
        if (meta.rows && meta.rows.length) {
            html += `
                <button class="table-toggle-btn" title="View interactive data table">
                    📋 View Data Table (${rowCount} rows)
                </button>
                <button class="csv-export-btn" title="Download data as CSV">
                    📥 Download CSV
                </button>
            `;
        }
        if (meta.sql) {
            html += `
                <button class="sql-toggle-btn" title="Toggle SQL query">
                    ⚡ Show SQL
                </button>
            `;
        }
        html += `</div>`;
        toolbar.innerHTML = html;

        if (meta.sql) {
            const sqlBox = document.createElement("div");
            sqlBox.className = "sql-preview-box";
            sqlBox.textContent = meta.sql;
            toolbar.appendChild(sqlBox);

            const sqlBtn = toolbar.querySelector(".sql-toggle-btn");
            if (sqlBtn) {
                sqlBtn.addEventListener("click", () => {
                    const isVis = sqlBox.classList.toggle("visible");
                    sqlBtn.textContent = isVis ? "Hide SQL" : "⚡ Show SQL";
                });
            }
        }

        if (meta.rows && meta.rows.length) {
            const tableBox = document.createElement("div");
            tableBox.className = "data-table-preview-container";
            
            const cols = meta.columns || Object.keys(meta.rows[0]);
            let tableHtml = `<div class="data-table-scroll"><table class="data-preview-table"><thead><tr>`;
            for (const col of cols) {
                tableHtml += `<th>${escapeHtml(col.replace(/_/g, ' '))}</th>`;
            }
            tableHtml += `</tr></thead><tbody>`;
            for (const row of meta.rows) {
                tableHtml += `<tr>`;
                for (const col of cols) {
                    const val = row[col] !== null && row[col] !== undefined ? row[col] : '';
                    tableHtml += `<td>${escapeHtml(String(val))}</td>`;
                }
                tableHtml += `</tr>`;
            }
            tableHtml += `</tbody></table></div>`;
            tableBox.innerHTML = tableHtml;
            toolbar.appendChild(tableBox);

            const tableBtn = toolbar.querySelector(".table-toggle-btn");
            if (tableBtn) {
                tableBtn.addEventListener("click", () => {
                    const isVis = tableBox.classList.toggle("visible");
                    tableBtn.textContent = isVis 
                        ? `📋 Hide Data Table (${rowCount} rows)` 
                        : `📋 View Data Table (${rowCount} rows)`;
                });
            }

            const csvBtn = toolbar.querySelector(".csv-export-btn");
            if (csvBtn) {
                csvBtn.addEventListener("click", () => {
                    downloadCSV("markazi_export", cols, meta.rows);
                });
            }
        }

        container.appendChild(toolbar);
    }

    function downloadCSV(filename, columns, rows) {
        if (!rows || !rows.length) return;
        const header = columns.join(",");
        const csvRows = rows.map(r => columns.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(","));
        const csvContent = "data:text/csv;charset=utf-8," + [header, ...csvRows].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `${filename}_${Date.now()}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    }


    function formatMarkdown(text) {
        if (!text) return "";
        let html = escapeHtml(text);
        
        // Bold (**text**)
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Inline Code (`text`)
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Clean line breaks and bullet lists
        const lines = html.split("\n");
        let formatted = "";
        let inList = false;

        for (let line of lines) {
            line = line.trim();
            if (!line) {
                if (inList) { formatted += "</ul>"; inList = false; }
                continue;
            }
            if (line.startsWith("### ")) {
                if (inList) { formatted += "</ul>"; inList = false; }
                formatted += `<h3 class="chunk-heading">${line.substring(4)}</h3>`;
            } else if (line.startsWith("## ")) {
                if (inList) { formatted += "</ul>"; inList = false; }
                formatted += `<h2 class="chunk-heading-lg">${line.substring(3)}</h2>`;
            } else if (line.startsWith("- ") || line.startsWith("* ")) {
                if (!inList) { formatted += "<ul class='chunk-list'>"; inList = true; }
                formatted += `<li>${line.substring(2)}</li>`;
            } else {
                if (inList) { formatted += "</ul>"; inList = false; }
                formatted += `<p>${line}</p>`;
            }
        }
        if (inList) formatted += "</ul>";
        return formatted;
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function scrollToBottom() {
        if (chatViewport) {
            chatViewport.scrollTop = chatViewport.scrollHeight;
        }
    }

    // --- On Initial Page Load: Restore session if available ---
    try {
        const savedCurrentId = localStorage.getItem(STORAGE_KEY_CURRENT);
        if (savedCurrentId) {
            const sessions = getStoredSessions();
            const session = sessions.find(s => s.id === savedCurrentId);
            if (session && session.messages && session.messages.length) {
                loadSession(session);
            }
        }
    } catch (e) {
        console.error("Error restoring session:", e);
    }
});
