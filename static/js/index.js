// ========== WEEKLY EXPENSE CHART ==========
async function loadWeeklyChart() {
    try {
        const response = await fetch("/api/monthly-expense-chart");
        const data = await response.json();

        const ctx = document.getElementById("mainChart");
        if (ctx) {
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Weekly Expenses",
                        data: data.data,
                        borderColor: "#6366f1",
                        backgroundColor: "rgba(99, 102, 241, 0.1)",
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: "#6366f1"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { 
                        legend: { display: true },
                        title: { display: false }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { color: "#888" }
                        },
                        x: {
                            ticks: { color: "#888" }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error("Error loading weekly chart: - index.js:45", error);
    }
}

// ========== CATEGORY COMPARISON CHART ==========
async function loadCategoryChart() {
    try {
        const response = await fetch("/api/category-comparison");
        const data = await response.json();

        const ctx = document.getElementById("categoryChart");
        if (ctx) {
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.categories,
                    datasets: [
                        {
                            label: "Last Month",
                            data: data.last_month,
                            backgroundColor: "rgba(239, 68, 68, 0.7)",
                            borderColor: "#ef4444",
                            borderWidth: 2
                        },
                        {
                            label: "This Month",
                            data: data.this_month,
                            backgroundColor: "rgba(34, 197, 94, 0.7)",
                            borderColor: "#22c55e",
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { 
                        legend: { display: true },
                        title: { display: false }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { color: "#888" }
                        },
                        x: {
                            ticks: { color: "#888" }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error("Error loading category chart: - index.js:98", error);
    }
}

// Load both charts when page loads
document.addEventListener("DOMContentLoaded", function() {
    loadWeeklyChart();
    loadCategoryChart();
});