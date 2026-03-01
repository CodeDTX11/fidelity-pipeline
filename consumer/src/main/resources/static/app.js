const transactionsBody = document.getElementById("transactions-body");
const feedbackBanner = document.getElementById("feedback-banner");
const refreshButton = document.getElementById("refresh-button");
const rowCount = document.getElementById("row-count");
const lastRefresh = document.getElementById("last-refresh");
const statusPill = document.getElementById("status-pill");

function formatTimestamp(value) {
    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short"
    }).format(new Date(value));
}

function formatPrice(value) {
    return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: "USD"
    }).format(value);
}

function renderRows(transactions) {
    if (transactions.length === 0) {
        transactionsBody.innerHTML = `
            <tr class="placeholder-row">
                <td colspan="8">No transactions found.</td>
            </tr>
        `;
        return;
    }

    transactionsBody.innerHTML = transactions.map((transaction) => `
        <tr>
            <td>${transaction.eventId}</td>
            <td>${formatTimestamp(transaction.eventTs)}</td>
            <td>${transaction.customerId}</td>
            <td>${transaction.symbol}</td>
            <td>
                <span class="side-pill ${transaction.side.toLowerCase()}">${transaction.side}</span>
            </td>
            <td>${transaction.quantity}</td>
            <td>${formatPrice(transaction.price)}</td>
            <td>${transaction.sourceFile ?? ""}</td>
        </tr>
    `).join("");
}

function showError(message) {
    feedbackBanner.hidden = false;
    feedbackBanner.textContent = message;
}

function clearError() {
    feedbackBanner.hidden = true;
    feedbackBanner.textContent = "";
}

async function loadTransactions() {
    refreshButton.disabled = true;
    statusPill.textContent = "Refreshing";

    try {
        const response = await fetch("/api/transactions", {
            headers: {
                Accept: "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`Request failed with status ${response.status}`);
        }

        const transactions = await response.json();
        renderRows(transactions);
        rowCount.textContent = String(transactions.length);
        lastRefresh.textContent = new Date().toLocaleTimeString();
        statusPill.textContent = "Ready";
        clearError();
    } catch (error) {
        statusPill.textContent = "Error";
        showError(`Unable to load transactions. ${error.message}`);
    } finally {
        refreshButton.disabled = false;
    }
}

refreshButton.addEventListener("click", loadTransactions);

loadTransactions();
