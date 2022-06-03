const $password_modal = $('#password-changed')      // Password change modal
const $canv_quota = $('#chart-quota')               // Quota chart canvas

// Charts
const quota_chart = createQuotaChart()

// Form
const $password_form = $('#password-change-form')


function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}


function createQuotaChart() {

    // Data
    const datasets = {
        labels: [],
        datasets: [{
            label: "Dataset quota",
            data: []
        }]
    }

    const config = {
        type: 'doughnut',
        data: datasets,
        options: {
            layout: {
                padding: 20
            },
            responsive: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';

                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed !== null) {
                                label += formatBytes(context.parsed)
                            }
                            return label;
                        }
                    }
                }
            }
        }
    }


    return new Chart(
        document.getElementById('chart-quota'),
        config
    )
}


function updateQuotaChart(data) {
    // Get labels (datasets + free)
    const labels = Object.keys(data.quota_used)
    labels.push("free")
    const values = Object.values(data.quota_used)
    values.push(data.quota_free)

    // Colors
    let color_scheme = new ColorScheme
    color_scheme.from_hex('99ff00')
        .scheme('triade')
        .distance(0.36)
        .variation('pastel')
    let unordered = color_scheme.colors().map(s => '#' + s)        // prepend # for chartjs
    const colors = []
    for (let i = 0; i < unordered.length; i++) {
        colors.push(unordered[(4 * i) % unordered.length])      // reorder colors for a better contrast
    }

    // Update chart
    quota_chart.data.labels = labels
    quota_chart.data.datasets[0].data = values
    quota_chart.data.datasets[0].backgroundColor = colors
    quota_chart.update()
}


(function () {
    // Show modal for successful password change
    if (show_modal) {
        let modal = new bootstrap.Modal($password_modal.get(0), {})
        modal.show()
    }

    // Get and show quota in chart
    $.getJSON(quota_url, updateQuotaChart)
})()