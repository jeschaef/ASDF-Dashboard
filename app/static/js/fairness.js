const $status = $('#task-status')       // Task status alert
const $submit = $('#task-submit')       // Submit button (note: does not submit form)
const $switch = $('#switch')            // Positive class switch (0/1)
const $slider = $('#threshold')         // Entropy threshold (0 <= t <= 1)
const $canv_fair = $('#chart-fair')     // Canvas for fair chart
const $canv_group = $('#chart-group')   // Canvas for group chart

// Create empty charts
let result = null                       // Global variable to hold fairness analysis result
const fair_chart = createFairChart()
const group_chart = createGroupChart()

// Table
const $table = $('#table-groups')


function parseFairnessResult() {
    // General fairness data
    const fair = JSON.parse(result['fair'])
    const abs_means = fair['abs_mean']

    // Clustering-based fairness data
    const c_acc = JSON.parse(result['c_acc'])
    const c_data = [c_acc['mean_err'], abs_means['c_stat_par'], abs_means['c_eq_opp'],
        abs_means['c_avg_odds'], abs_means['c_acc']]

    // Entropy-based (groups) fairness data
    const g_acc = JSON.parse(result['g_acc'])
    const g_data = [g_acc['mean_err'], abs_means['g_stat_par'], abs_means['g_eq_opp'],
        abs_means['g_avg_odds'], abs_means['g_acc']]

    return [c_data, g_data]
}


function createFairChart() {

    // Display absolute mean errors of each category
    const labels = [
        'Accuracy Error',
        'Statistical Parity',
        'Equal Opportunity',
        'Equalized odds',
        'Accuracy',
    ];

    // Define datasets (empty)
    const datasets = {
        labels: labels,
        datasets: [{
            label: 'Clustering-based Fairness',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgb(255, 99, 132)',
            pointBackgroundColor: 'rgb(255, 99, 132)',
            pointHoverBorderColor: 'rgb(255, 99, 132)',
            data: [],
        }, {
            label: 'Entropy-based Fairness',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            pointBackgroundColor: 'rgb(54, 162, 235)',
            pointHoverBorderColor: 'rgb(54, 162, 235)',
            data: [],
        }]
    };

    // Chart config
    const config = {
        type: 'radar',
        data: datasets,
        options: {
            layout: {
                padding: 20
            },
            elements: {
                line: {
                    borderWidth: 3,
                    spanGaps: true
                },
                point: {
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                }
            },
            scales: {
                r: {
                    suggestedMin: 0,
                    suggestedMax: 1
                }
            }
        }
    };

    // Create chart
    return new Chart(
        document.getElementById('chart-fair'),
        config
    )
}


function createGroupChart() {


    // Define datasets (empty)
    const datasets = {
        labels: [],
        datasets: [{
            label: 'Clusters',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 1,
            borderRadius: 1,
            data: [],
        }, {
            label: 'Entropy-based Subgroups',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1,
            borderRadius: 1,
            data: [],
            skipNull: true,     // duplicates are omitted
        }]
    };

    // Chart config
    const config = {
        type: 'bar',
        data: datasets,
        options: {
            layout: {
                padding: 20
            },
            maintainAspectRatio: false,         // Chart will be much wider some times
        }
    };

    // Create chart
    return new Chart(
        document.getElementById('chart-group'),
        config
    )
}


function updateFairChart(chart) {
    const [c_data, g_data] = parseFairnessResult()
    chart.data.datasets[0].data = c_data
    chart.data.datasets[1].data = g_data
    chart.update();
}


function updateGroupChart(chart, k) {
    // Clusters
    const counts = countValues(result.clustering)

    // Entropy-based subgroups
    const group_sizes = result.group_sizes

    // Update chart
    chart.data.labels = [...counts.keys()]      // [0,1,2,...,k-1]
    chart.data.datasets[0].data = counts
    chart.data.datasets[1].data = group_sizes

    // Reset size based on k
    const barpx = 30
    const extra = 200
    const width = k * barpx + extra
    chart.canvas.parentNode.style.width = width + 'px';

    chart.update()

}


function clearChart(chart) {
    chart.data.datasets.forEach((dataset) => {
        dataset.data.pop();
    });
    chart.update();
}


function showStatus(status_msg, fades = false) {
    $status.show()
    $status.text(status_msg)
    if (fades)
        $status.fadeOut(3000)   // slowly fade out in 3s
}


function startFairnessTask(event) {

    // Display information
    showStatus("Starting fairness task ...")

    // Create request data
    const dataset_id = $("#dataset-select").find(":selected").val()
    const positive_class = ($switch.is(":checked") ? 1 : 0)
    const threshold = $slider.val()

    const data = {
        dataset_id: dataset_id,
        positive_class: positive_class,
        threshold: threshold,
    }

    // Send ajax POST request to start the task
    $.post(start_task_url,
        data,
        function (data, status, request) {
            const status_url = request.getResponseHeader('Location');
            updateProgress(status_url);
        }
    ).done(function () {
        // alert('Done!')
    }).fail(function () {
        alert('Failed!')
    })
}


function updateProgress(status_url) {
    // Send a get request to the status_url
    $.getJSON(status_url, function (data) {

        // Update status info
        const state = data['state']
        const status = data['status']
        const is_success = (state == 'SUCCESS')
        showStatus("State=" + state + ": " + status, is_success)    // fade if success

        // Switch states
        if (state == 'SUCCESS') {

            result = JSON.parse(data['result'])
            displayResult()


        } else if (state == 'FAILURE') {

            // TODO error

        } else {

            // Task is pending or in progress --> restart status update (after 2s timeout)
            setTimeout(function () {
                updateProgress(status_url)
            }, 2000)

        }

    })
}


function displayResult() {
    console.log("Finished:", result)

    console.log(JSON.parse(result.c_acc))

    console.log(JSON.parse(result.subgroups))

    // Plot subgroup fairness data
    updateFairChart(fair_chart)

    // Plot clustering/entropy-based groups data
    const k = Math.max(...result.clustering) + 1
    updateGroupChart(group_chart, k)

    // Subgroups
    const subgroups = JSON.parse(result.subgroups)
    const data = []
    const cols = Object.keys(subgroups)
    for (let i = 0; i < k; i++) {
        let group = {id: i}
        for (const c of cols) {
            group[c] = subgroups[c][i]
        }
        data.push(group)
    }
    console.log(data)

    // Init table
    initTable(data, result)

}


function countValues(arr) {
    const k = Math.max(...arr) + 1
    const counts = new Array(k).fill(0)     // TODO outliers
    for (const e of arr)
        counts[e] = counts[e] + 1
    return counts
}


function initTable(data) {
    // Columns (table header)
    const columns = []
    for (const c in data[0]) {
        columns.push({title: c, field: c, detailFormatter: detailFormatter})
    }

    // Init bootstrap-table
    $table.bootstrapTable({columns: columns, data: data})
}


function detailFormatter(index, row, $element) {
    // Parse raw data
    const raw_data = JSON.parse(result.raw)
    const raw_keys = Object.keys(raw_data)

    // Construct result string
    let s = "Row " + index + ": "
    for (const k of raw_keys) {
        s = s + k + "=" + raw_data[k][index] + " "
    }
    // return s

    // Table element
    const $sub_table = $('<table></table>')
    $sub_table.attr("id", "detail-table" + index)

    // Add table header (impossible via bootstrapTable({columns: ...}) with rowspan/colspan)
    const $tr_upper = $('<tr></tr>')
    $tr_upper.append(
        $('<th colspan="4">Cluster-based subgroup</th>'),
        $('<th colspan="4">Entropy-based subgroup</th>')
    )

    const $tr_lower = $('<tr></tr>')
    $tr_lower.append(
        $('<th data-field="c_stat_par">Stat. Parity</th>'),
        $('<th data-field="c_eq_opp">Eq. Opportunity</th>'),
        $('<th data-field="c_avg_odds">(Avg.) Eq. Odds</th>'),
        $('<th data-field="c_acc">Accuracy</th>'),
        $('<th data-field="g_stat_par">Stat. Parity</th>'),
        $('<th data-field="g_eq_opp">Eq. Opportunity</th>'),
        $('<th data-field="g_avg_odds">(Avg.) Eq. Odds</th>'),
        $('<th data-field="g_acc">Accuracy</th>')
    )
    const $thead = $('<thead></thead>')
    $thead.append($tr_upper, $tr_lower)
    $sub_table.append($thead)
    console.log($sub_table)

    // Add the table element to the cell
    $element.append($sub_table)

    // Init bootstrap table
    $sub_table.bootstrapTable({data: []})
}


$(function () {
    // Hide status alert at the start
    $status.hide()

    // Add button functionality (submit task)
    $submit.click(startFairnessTask)

    // Update switch label text on change (positive class)
    $switch.change(function () {
        let $label = $("label[for='" + $(this).attr('id') + "']");
        const positive_class = ($(this).is(":checked") ? 1 : 0)
        $label.text("Positive class label: " + positive_class)
    })

    // Update slider label text on change (entropy threshold)
    $slider.on('input', function () {
        let $label = $("label[for='" + $(this).attr('id') + "']");
        const threshold = $(this).val()
        $label.text("Entropy threshold: " + threshold)
    })

    // Add click listener on group chart (bar)
    $canv_group.click(function (evt) {
        const elem = group_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: false}, true)
        if (elem && elem.length === 1) {
            const dataset = elem[0].datasetIndex
            const index = elem[0].index
            console.log("Dataset:", dataset, "Index:", index)
        }
    })

    // Add click listener on fair chart (radar)
    $canv_fair.click(function (evt) {
        const elem = fair_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: false}, true)
        if (elem && elem.length === 1) {
            const dataset = elem[0].datasetIndex
            const index = elem[0].index
            console.log("Dataset:", dataset, "Index:", index)
        }
    })

});
