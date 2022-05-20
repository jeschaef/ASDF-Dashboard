const $status = $('#task-status')           // Task status alert
const $area = $('#chart-area')              // Div parent container of charts/tables with results
const $submit = $('#task-submit')           // Submit button (note: does not submit form)
const $switch = $('#switch')                // Positive class switch (0/1)
const $slider = $('#threshold')             // Entropy threshold (0 <= t <= 1)
const $canv_fair = $('#chart-fair')         // Canvas for fair chart
const $canv_group = $('#chart-group')       // Canvas for group chart
const $canv_select = $('#chart-select')     // Canvas for selection chart

// Create empty charts
let result = null                           // Global variable to hold fairness analysis result
const fair_chart = createFairChart()
const group_chart = createGroupChart()
const select_chart = createSelectionChart()

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


function parseSelectionData(index) {
    // Parse raw data
    const raw_data = JSON.parse(result.raw)
    const c_data = [raw_data.c_stat_par[index],
        raw_data.c_eq_opp[index],
        raw_data.c_avg_odds[index],
        raw_data.c_acc[index]]
    const g_data = [raw_data.g_stat_par[index],
        raw_data.g_eq_opp[index],
        raw_data.g_avg_odds[index],
        raw_data.g_acc[index]]
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


function updateFairChart() {
    const [c_data, g_data] = parseFairnessResult()
    fair_chart.data.datasets[0].data = c_data
    fair_chart.data.datasets[1].data = g_data
    fair_chart.update();
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


function updateGroupChart(k) {
    // Clusters
    const counts = countValues(result.clustering)

    // Entropy-based subgroups
    const group_sizes = result.group_sizes

    // Update chart
    group_chart.data.labels = [...counts.keys()]      // [0,1,2,...,k-1]
    group_chart.data.datasets[0].data = counts
    group_chart.data.datasets[1].data = group_sizes

    // Reset size based on k
    const barpx = 30
    const extra = 200
    const width = k * barpx + extra
    group_chart.canvas.parentNode.style.width = width + 'px';

    group_chart.update()

}


function createSelectionChart() {
    const labels = [
        'Statistical Parity',
        'Equal Opportunity',
        'Equalized odds',
        'Accuracy',
    ];

    // Define datasets (empty)
    const datasets = {
        labels: labels,
        datasets: [{
            label: 'Cluster',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 1,
            borderRadius: 1,
            data: [],
        }, {
            label: 'Entropy-based Subgroup',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1,
            borderRadius: 1,
            data: []
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
            plugins: {
                title: {
                    display: true,
                    text: "Subgroup fairness metrics for selected cluster/entropy-based subgroup"
                }
            }
        }
    };

    // Create chart
    return new Chart(
        document.getElementById('chart-select'),
        config
    )
}


function updateSelectionChart(index) {
    const [c_data, g_data] = parseSelectionData(index)
    select_chart.data.datasets[0].data = c_data
    select_chart.data.datasets[1].data = g_data
    select_chart.options.plugins.title.text =
        "Subgroup fairness metrics for cluster/entropy-based subgroup " + index
    select_chart.update();
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
            const status_url = request.getResponseHeader('status');
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

    // Show chart area
    $area.show()

    // Plot subgroup fairness data
    updateFairChart()

    // Plot clustering/entropy-based groups data
    const k = Math.max(...result.clustering) + 1
    updateGroupChart(k)

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
        $('<th data-field="c_stat_par" data-cell-style="cellStyleCluster">Stat. Parity</th>'),
        $('<th data-field="c_eq_opp" data-cell-style="cellStyleCluster">Eq. Opportunity</th>'),
        $('<th data-field="c_avg_odds" data-cell-style="cellStyleCluster">(Avg.) Eq. Odds</th>'),
        $('<th data-field="c_acc" data-cell-style="cellStyleCluster">Accuracy</th>'),
        $('<th data-field="g_stat_par" data-cell-style="cellStyleEntropy">Stat. Parity</th>'),
        $('<th data-field="g_eq_opp" data-cell-style="cellStyleEntropy">Eq. Opportunity</th>'),
        $('<th data-field="g_avg_odds" data-cell-style="cellStyleEntropy">(Avg.) Eq. Odds</th>'),
        $('<th data-field="g_acc" data-cell-style="cellStyleEntropy">Accuracy</th>')
    )
    const $thead = $('<thead></thead>')
    $thead.append($tr_upper, $tr_lower)
    $sub_table.append($thead)
    console.log($sub_table)

    // Add the table element to the cell
    $element.append($sub_table)

    // On click, display the selected subgroups fairness in the selection chart
    $element.click(function (evt) {
        updateSelectionChart(index)
    })

    // Table data
    let tab_row = {
        "c_stat_par": raw_data.c_stat_par[index],
        "c_eq_opp": raw_data.c_eq_opp[index],
        "c_avg_odds": raw_data.c_avg_odds[index],
        "c_acc": raw_data.c_acc[index],
        "g_stat_par": raw_data.g_stat_par[index],
        "g_eq_opp": raw_data.g_eq_opp[index],
        "g_avg_odds": raw_data.g_avg_odds[index],
        "g_acc": raw_data.g_acc[index]
    }

    // Init bootstrap table
    $sub_table.bootstrapTable({data: [tab_row]})
}


function cellStyleCluster(value, row, index, field) {
    return {
        css: {
            'background-color': 'rgba(255, 99, 132, 0.2)'
        }
    }
}


function cellStyleEntropy(value, row, index, field) {
    return {
        css: {
            'background-color': 'rgba(54, 162, 235, 0.2)'
        }
    }
}


$(function () {
    // Hide status alert & chart area at the start
    $status.hide()
    $area.hide()

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

            // Scroll to page & row for selected subgroup
            const page_size = $table.bootstrapTable('getOptions').pageSize
            const goto_page = Math.floor(index / page_size) + 1         // page numbers start at 1 not 0...
            const scroll_index = index % page_size
            $table.bootstrapTable('selectPage', goto_page)
            $table.bootstrapTable('scrollTo', {unit: 'rows', value: scroll_index})

            // Show bars for selected subgroup
            updateSelectionChart(index)
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

