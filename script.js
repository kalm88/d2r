const overlay = document.getElementById('overlay');
const runNotes = document.getElementById('runNotes');
const timerStatus = document.getElementById('timerStatus');
const timerToggle = document.getElementById('timerToggle');
const timerHotkeyInput = document.getElementById('timerHotkey');
const hotkeyStatus = document.getElementById('hotkeyStatus');
const enableLootAssist = document.getElementById('enableLootAssist');
const lootAssistStatus = document.getElementById('lootAssistStatus');
const diablo2ioFrame = document.getElementById('diablo2ioFrame');
const browserStatus = document.getElementById('browserStatus');
const openDiablo2io = document.getElementById('openDiablo2io');
const reloadDiablo2io = document.getElementById('reloadDiablo2io');

let timerInterval = null;
let timerStart = null;
let timerHotkey = (timerHotkeyInput.value || 't').toLowerCase();

function updateTimer() {
  if (!timerStart) return;
  const elapsedMs = Date.now() - timerStart;
  const totalSeconds = Math.floor(elapsedMs / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  timerStatus.textContent = `Timer: ${minutes}:${seconds}`;
}

function syncHotkeyText() {
  hotkeyStatus.innerHTML = `Press <kbd>${timerHotkey.toUpperCase()}</kbd> to start/stop timer.`;
}

function toggleTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
    timerStart = null;
    timerStatus.textContent = 'Timer: stopped';
    timerToggle.textContent = 'Start Timer';
  } else {
    timerStart = Date.now();
    timerInterval = setInterval(updateTimer, 250);
    timerToggle.textContent = 'Stop Timer';
  }
}

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('click', () => {
    const action = button.dataset.action;

    if (action === 'note') {
      const stamp = new Date().toLocaleTimeString();
      runNotes.value += `${runNotes.value ? '\n' : ''}[${stamp}] `;
      runNotes.focus();
    }

    if (action === 'clear') {
      runNotes.value = '';
    }

    if (action === 'timer') {
      toggleTimer();
    }
  });
});

timerHotkeyInput.addEventListener('input', (event) => {
  const value = event.target.value.trim().toLowerCase();
  if (!value) {
    return;
  }

  timerHotkey = value[0];
  event.target.value = timerHotkey;
  syncHotkeyText();
});

window.addEventListener('keydown', (event) => {
  const pressedKey = event.key.toLowerCase();

  if (pressedKey === 'o') {
    overlay.classList.toggle('hidden');
  }

  if (pressedKey === timerHotkey) {
    toggleTimer();
  }
});

function updateLootAssistState() {
  if (enableLootAssist.checked) {
    lootAssistStatus.textContent = 'Loot assist enabled. Placeholder mode active until in-game color reading is integrated.';
  } else {
    lootAssistStatus.textContent = 'Loot assist is disabled. (Scaffold only: color-reading integration is planned.)';
  }
}

function loadDiablo2io() {
  diablo2ioFrame.src = 'https://diablo2.io/';
  browserStatus.textContent = 'Trying to load diablo2.io in-panel. If blocked by site security policy, use the Open button for full interaction.';
}

openDiablo2io.addEventListener('click', () => {
  window.open('https://diablo2.io/', '_blank', 'noopener,noreferrer');
});

reloadDiablo2io.addEventListener('click', loadDiablo2io);

diablo2ioFrame.addEventListener('load', () => {
  browserStatus.textContent = 'diablo2.io loaded in the panel (if permitted by iframe policy).';
});

enableLootAssist.addEventListener('change', updateLootAssistState);

let activePanel = null;
let offsetX = 0;
let offsetY = 0;

document.querySelectorAll('[data-panel]').forEach((panel) => {
  panel.addEventListener('mousedown', (event) => {
    const targetTag = event.target.tagName.toLowerCase();
    if (
      targetTag === 'textarea' ||
      targetTag === 'button' ||
      targetTag === 'input' ||
      targetTag === 'label' ||
      targetTag === 'iframe'
    ) {
      return;
    }

    activePanel = panel;
    const rect = panel.getBoundingClientRect();
    offsetX = event.clientX - rect.left;
    offsetY = event.clientY - rect.top;
    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
    panel.style.transform = 'none';
  });
});

document.addEventListener('mousemove', (event) => {
  if (!activePanel) return;
  activePanel.style.left = `${event.clientX - offsetX}px`;
  activePanel.style.top = `${event.clientY - offsetY}px`;
});

document.addEventListener('mouseup', () => {
  activePanel = null;
});

syncHotkeyText();
updateLootAssistState();
loadDiablo2io();
