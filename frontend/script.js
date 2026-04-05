/* 🛡️ SHIELD AI v2.5 - CORE SPA ENGINE */
let deferredPrompt;

// 📲 PWA INSTALLATION logic (unchanged)
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
});

async function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            document.getElementById('pwa-install-btn').style.display = 'none';
        }
        deferredPrompt = null;
    }
}

// Show Install button when app can be installed
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const btn = document.getElementById('pwa-install-btn');
    if (btn) btn.style.display = 'block';
});

// 2. 📊 FRAUD ANALYSIS PIPELINE
document.getElementById('auditForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('subBtn');
    const resBox = document.getElementById('resBox');

    btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> ANALYZING...';
    lucide.createIcons();

    const amt = parseFloat(document.getElementById('amt').value) || 0;
    const hour = parseInt(document.getElementById('txnHour').value) || 12;
    const isIntl = document.getElementById('cardType').value === 'international';
    const sId = localStorage.getItem('shield_id') || 'Deep Halder';

    setTimeout(async () => {
        try {
            const res = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amt, hour: hour, is_international: isIntl, owner: sId })
            });


            if (!res.ok) throw new Error("Server Reject: Status " + res.status);
            const data = await res.json();

            resBox.style.display = 'block';
            const isFraud = (data.fraud_index === 1);
            const score = data.confidence_score || 0;

            if (isFraud) {
                resBox.innerHTML = `⚠️ DANGER: HIGH PROBABILITY OF FRAUD (${score.toFixed(1)}%)`;
                resBox.style.background = 'rgba(244, 63, 94, 0.2)';
                resBox.style.color = '#f43f5e';
                showLockdown();
            } else {
                resBox.innerHTML = `✅ CLEAR: TRANSACTION VERIFIED (${score.toFixed(1)}% Risk)`;
                resBox.style.background = 'rgba(16, 185, 129, 0.2)';
                resBox.style.color = '#10b981';
            }

            // Visual graph spike
            if (window.threatChart) {
                const ds = window.threatChart.data.datasets[0];
                ds.data[ds.data.length - 1] = isFraud ? 95 : 15;
                ds.borderColor = isFraud ? '#f43f5e' : '#06b6d4';
                window.threatChart.update();
                setTimeout(() => { ds.borderColor = '#06b6d4'; window.threatChart.update(); }, 2000);
            }
        } catch (err) {
            console.error("Shield Failure:", err);
            resBox.innerHTML = "❌ AI ENGINE OFFLINE (Check Connection)";
            resBox.style.display = 'block';
        }
        btn.innerHTML = 'IDENTIFY THREAT';
        lucide.createIcons();
        refreshAlerts();
    }, 1200);
});

function showLockdown() {
    document.getElementById('lockdown').style.display = 'flex';
    setTimeout(() => { document.getElementById('lockdown').style.display = 'none'; }, 5000);
}

// 🔔 ACTIVITY FEED (SPA Logic)
let allAlerts = [];

async function refreshAlerts() {
    const list = document.getElementById('txn-list');
    const sId = localStorage.getItem('shield_id') || 'Deep Halder';
    const profileName = document.getElementById('profile-name');
    if (profileName) profileName.innerText = sId;

    try {
        const res = await fetch('/api/alerts?user=' + encodeURIComponent(sId));
        allAlerts = await res.json();
        renderFilteredAlerts(allAlerts);
        updateTrendsFromHistory(allAlerts);
    } catch (err) { console.error("Feed Error:", err); }
}

function filterAlerts() {
    const q = document.getElementById('txnSearch').value.toLowerCase();
    const filtered = allAlerts.filter(a => 
        a.amt.toString().includes(q) || 
        a.status.toLowerCase().includes(q) || 
        a.time.toLowerCase().includes(q)
    );
    renderFilteredAlerts(filtered);
}

function renderFilteredAlerts(data) {
    const list = document.getElementById('txn-list');
    list.innerHTML = data.map(a => `
        <div class="glass-card alert-item" style="border-left: 4px solid ${a.status === 'FRAUD' || a.status.includes('FLAGGED') ? '#f43f5e' : '#10b981'}; margin-bottom:1rem; padding:1.2rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <p style="font-weight:800; font-size:15px; display:flex; align-items:center; gap:6px;">
                    ₹${a.amt.toLocaleString()}
                    ${(a.status === 'FRAUD' || a.status.includes('FLAGGED')) ? '<span style="background:rgba(244,63,94,0.1); color:#f43f5e; font-size:9px; padding:2px 6px; border-radius:10px;">FRAUD</span>' : '<span style="background:rgba(16,185,129,0.1); color:#10b981; font-size:9px; padding:2px 6px; border-radius:10px;">LEGIT</span>'}
                </p>
                <p style="font-size:11px; opacity:0.6; margin-top:2px;">${a.time} · Conf: ${a.conf}%</p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:10px; opacity:0.3; font-weight:700;">#${a.id}</div>
                <i data-lucide="${(a.status === 'FRAUD' || a.status.includes('FLAGGED')) ? 'alert-triangle' : 'check-circle'}" style="width:20px; color:${(a.status === 'FRAUD' || a.status.includes('FLAGGED')) ? '#f43f5e' : '#10b981'}; margin-top:4px;"></i>
            </div>
        </div>
    `).join('') || '<p style="text-align:center; padding:3rem; opacity:0.3; font-size:0.9rem;">No transactions found.</p>';
    lucide.createIcons();
}

async function clearAllAlerts() {
    const sId = localStorage.getItem('shield_id') || 'Deep Halder';
    await fetch('/api/alerts?user=' + encodeURIComponent(sId), { method: 'DELETE' });
    refreshAlerts();
}

// 🌌 NEURAL PARTICLE ENGINE (Aesthetic)
function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.onresize = resize;
    resize();

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.size = Math.random() * 1.5;
        }
        update() {
            this.x += this.vx; this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(6, 182, 212, 0.4)'; ctx.fill();
        }
    }

    for (let i = 0; i < 60; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update(); p.draw();
            particles.forEach(p2 => {
                const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                if (dist < 100) {
                    ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 - dist/1000})`;
                    ctx.lineWidth = 0.5; ctx.stroke();
                }
            });
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// 📈 REAL-TIME TRENDS ENGINE
// 🌌 NEURAL PARTICLE ENGINE (Aesthetic)
function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.onresize = resize;
    resize();

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.size = Math.random() * 1.5;
        }
        update() {
            this.x += this.vx; this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(6, 182, 212, 0.4)'; ctx.fill();
        }
    }

    for (let i = 0; i < 50; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update(); p.draw();
            particles.forEach(p2 => {
                const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                if (dist < 100) {
                    ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 - dist/800})`;
                    ctx.lineWidth = 0.5; ctx.stroke();
                }
            });
        });
        requestAnimationFrame(animate);
    }
    animate();
}

function initTrendsChart() {
    const ctx = document.getElementById('threatChart');
    const dCtx = document.getElementById('discreteChart');
    if (!ctx || !dCtx) return;
    
    // 1. Continuous Live Graph
    window.threatChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: Array(20).fill(''),
            datasets: [{
                label: 'Live Risk',
                data: Array(20).fill(10),
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                fill: true, tension: 0.4, borderWidth: 3, pointRadius: 0
            }]
        },
        options: {
            scales: { y: { min: 0, max: 100, display: false }, x: { display: false } },
            plugins: { legend: { display: false } },
            maintainAspectRatio: false,
            responsive: true,
            animation: { duration: 800 }
        }
    });

    // 2. Discrete Bar Graph (The "Not Movable" Static View)
    window.discreteChart = new Chart(dCtx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: Array(15).fill(''),
            datasets: [{
                label: 'Detection (0-1)',
                data: Array(15).fill(0),
                backgroundColor: '#6366f1',
                borderRadius: 4,
                barThickness: 20
            }]
        },
        options: {
            scales: { 
                y: { min: 0, max: 1.2, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { stepSize: 1, color: 'rgba(255,255,255,0.3)', font: { size: 10 } } },
                x: { grid: { display: false }, ticks: { display: false } }
            },
            plugins: { 
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => ctx.raw === 1 ? 'FRAUD DETECTED' : 'LEGITIMATE' } }
            },
            maintainAspectRatio: false,
            responsive: true
        }
    });
}

function updateTrendsFromHistory(data) {
    if (!window.threatChart || !window.discreteChart) return;
    
    // Reverse data to show chronological order
    const history = [...data].reverse().slice(-15);
    const riskScores = history.map(a => a.conf);
    const binaryStatus = history.map(a => (a.status === 'FRAUD' || a.status.includes('FLAGGED')) ? 1 : 0);
    
    // Update Continuous Chart (Remains as Confidence %)
    const paddedLine = [...riskScores];
    while (paddedLine.length < 20) paddedLine.unshift(5);
    
    const ds = window.threatChart.data.datasets[0];
    ds.data = paddedLine;
    const avgRisk = riskScores.reduce((a, b) => a + (b || 0), 0) / (riskScores.length || 1);
    ds.borderColor = avgRisk > 40 ? '#f43f5e' : '#06b6d4';
    window.threatChart.update('none');

    // Update Discrete Bar Chart (NOW BINARY 0-1)
    const barDs = window.discreteChart.data.datasets[0];
    barDs.data = binaryStatus;
    barDs.backgroundColor = history.map(a => 
        (a.status === 'FRAUD' || a.status.includes('FLAGGED')) ? '#f43f5e' : '#6366f1'
    );
    window.discreteChart.update();
}

function fullLogout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// INIT
window.onload = () => {
    lucide.createIcons();
    initTrendsChart();
    initParticles();
    const sId = localStorage.getItem('shield_id');
    const uDisp = document.getElementById('user-display-name');
    if (uDisp) uDisp.innerText = sId || 'GUEST';
    refreshAlerts();

    // Mouse Tracking for Radial Glow
    document.addEventListener('mousemove', e => {
        document.body.style.setProperty('--mouse-x', (e.clientX) + 'px');
        document.body.style.setProperty('--mouse-y', (e.clientY) + 'px');
    });
};

function shareSecureID() {
    const sId = localStorage.getItem('shield_id') || 'Deep Halder';
    const text = `🛡️ SHIELD AI — SECURE TERMINAL\n✅ User: ${sId}\n✅ Status: HYPER-SECURE\n\nCheckout my AI-driven Fraud Detection system!`;
    
    if (navigator.share) {
        navigator.share({ title: 'Shield AI Secure ID', text: text, url: window.location.href });
    } else {
        navigator.clipboard.writeText(text);
        alert("✨ Secure ID Summary copied to clipboard for sharing!");
    }
}
