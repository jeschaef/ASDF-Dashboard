const $status = $('#task-status')               // Task status alert
const $area = $('#chart-area')                  // Div parent container of charts/tables with results
const $submit = $('#task-submit')               // Submit button (note: does not submit form)
const $auto_submit = $('#task-auto-submit')     // Submit button (automatic fairness evaluation)
const $dataset = $("#dataset-select")           // Dataset selection
const $switch = $('#switch')                    // Positive class switch (0/1)
const $slider = $('#threshold')                 // Entropy threshold (0 <= t <= 1)
const $categoricals = $('#select-categ')        // Categorical column selectpicker (multiselect)
const $algorithm = $('#select-algo')            // Clustering algorithm selectpicker
const $params = $('#parameter-button')          // Button for clustering algorithm parameters
const $modal_body = $('#parameter-modal-body')  // Clustering parameter modal body
const $clear_params = $('#parameter-clear')     // Clear algorithm params button
const $select_rank = $('#select-ranking')       // Ranking criterion selection
const $switch_rank = $('#switch-ranking-order') // Ascending/descending switch for ranking
const $form = $('#fairness-form')               // Full fairness form (dataset, threshold, class label, ...)

// Popovers
const popover_categ = new bootstrap.Popover(document.getElementById('popover-categ'))
const popover_params = new bootstrap.Popover(document.getElementById('popover-params'))

// Canvas
const $canv_fair = $('#chart-fair')         // Canvas for fair chart
const $canv_group = $('#chart-group')       // Canvas for group chart
const $canv_select = $('#chart-select')     // Canvas for selection chart
const $canv_ranking = $('#chart-ranking')  // Canvas of ranking chart

// Create empty charts
let result = null                           // Global variable to hold fairness analysis result
const fair_chart = createFairChart()
const group_chart = createGroupChart()
const select_chart = createSelectionChart()
const ranking_chart = createRankingChart()

// Table
const $table = $('#table-groups')

// Clustering algorithm info
let clustering_info = null


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
            },
            maintainAspectRatio: false,
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
    setChartHeight(fair_chart)
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
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function (context) {
                            // context = TooltipItem[]
                            let title = ""
                            if (context[0].datasetIndex === 0)
                                title = "Cluster "
                            else if (context[0].datasetIndex === 1)
                                title = "Subgroup "
                            return title + context[0].dataIndex
                        },
                        label: function (context) {
                            // context = TooltipItem
                            return "Size: " + context.parsed.y  // parsed stores x- and y-axis
                        }
                    }
                }
            }
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
    setChartHeight(group_chart)
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
            },
            maintainAspectRatio: false,
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
    setChartHeight(select_chart)
    select_chart.update();
}


function createRankingChart() {
    const labels = [1, 2, 3, 4, 5];

    // Define datasets (empty)
    const datasets = {
        labels: labels,
        datasets: [{
            label: 'Ranking',
            backgroundColor: 'rgba(99, 255, 138, 0.2)',
            borderColor: 'rgb(99, 255, 138)',
            borderWidth: 1,
            borderRadius: 1,
            data: [],
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
                    text: "Subgroup ranking"
                }
            },
            maintainAspectRatio: false,
        }
    };

    return new Chart(
        document.getElementById('chart-ranking'),
        config
    );
}


function updateRankingChart() {

    // Order by selection
    const selection = $select_rank.val()
    const is_ascending = !($switch_rank.is(":checked"))
    const raw_data = JSON.parse(result.raw)[selection]
    const [labels, values] = sortData(raw_data, is_ascending, 5)

    // Update chart
    ranking_chart.data.labels = labels.slice(0, 5)      // ids of top 5 clusters/subgroups
    ranking_chart.data.datasets[0].data = values.slice(0, 5)
    const outer_height = $('#ranking-config').outerHeight()     // subtract height of ranking config (header)
    setChartHeight(ranking_chart, 500 - outer_height)
    ranking_chart.update()
}


function sortData(data, ascending = true, top = 5) {
    let items = Object.keys(data).map(function (key) {
        return [key, data[key]]
    })
    if (ascending) {
        items.sort(function (first, second) {
            return (first[1] != null ? first[1] : Infinity) - (second[1] != null ? second[1] : Infinity)
        })
    } else {
        items.sort(function (first, second) {
            return (second[1] != null ? second[1] : -Infinity) - (first[1] != null ? first[1] : -Infinity)
        })
    }
    const labels = items.map(i => i.slice(0, 1)[0])
    const values = items.map(i => i.slice(1, 2)[0])
    return [labels, values]
}


function clearChart(chart) {
    chart.data.datasets.forEach((dataset) => {
        dataset.data.pop();
    });
    chart.update();
}


function setChartHeight(chart, height = 500) {
    chart.canvas.parentNode.style.height = height + 'px';
}


function showStatus(status_msg, fades = false) {
    $status.show()
    $status.text(status_msg)
    if (fades)
        $status.fadeOut(3000)   // slowly fade out in 3s
}


function startFairnessTask(is_manual) {

    // Validate form manually
    const is_valid = $form.get(0).reportValidity()
    if (!is_valid)
        return

    // Display information
    showStatus("Starting fairness task ...")

    // Create request data
    const dataset_id = $dataset.find(":selected").val()
    const positive_class = ($switch.is(":checked") ? 1 : 0)
    const threshold = $slider.val()
    const categ_columns = $categoricals.val()
    let [algorithm, parameters, values] = [null, null, null]
    if (is_manual) {
        algorithm = $algorithm.val()
        [parameters, values] = getClusteringParameters()
    } else {
        algorithm = 'agglomerative'
        parameters = ['linkage', 'n_clusters']     // TODO auto set n_clusters based on dataset size?
        values = ['single', 10]
    }

    const data = {
        dataset_id: dataset_id,
        positive_class: positive_class,
        threshold: threshold,
        categ_columns: categ_columns,
        algorithm: algorithm,
        parameters: parameters,
        values: values,
    }

    // Send POST request to start the task (as json)
    $.post(start_task_url, data,
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

    // Show chart area
    $area.show()

    // Plot subgroup fairness data
    updateFairChart()

    // Plot clustering/entropy-based groups data
    const k = Math.max(...result.clustering) + 1
    updateGroupChart(k)

    // Plot subgroup fairness for initial selection (cluster/subgroup 0)
    updateSelectionChart(0)

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

    // Init table
    initTable(data, result)

    // Plot top-5 ranking for selected criterion
    updateRankingChart($select_rank.val())
}


function countValues(arr) {
    const k = Math.max(...arr) + 1
    const counts = new Array(k).fill(0)     // TODO outliers
    for (const e of arr)
        counts[e] = counts[e] + 1
    return counts
}


function initTable(data) {
    // Collapse all expanded row details (old results are still displayed otherwise)
    $table.bootstrapTable('collapseAllRows')

    // Columns (table header)
    const columns = []
    for (const c in data[0]) {
        columns.push({title: c, field: c, detailFormatter: detailFormatter})
    }

    // Init bootstrap-table
    $table.bootstrapTable({columns: columns})
    $table.bootstrapTable('load', data)
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


function setDatasetColumns(data) {
    // Remove all previously set options
    $categoricals.find("option").remove().end()

    // Add columns as options
    const columns = Object.keys(data)
    for (const key of columns) {
        $categoricals.append($('<option value="' + key + '">' + key + '</option>'))
    }

    // Enable selectpicker, disable popover (tooltip)
    $categoricals.prop("disabled", false)
    popover_categ.disable()

    // Refresh
    $categoricals.selectpicker('refresh')
}


function initClusteringAlgorithms() {
    for (const key in clustering_info) {
        $algorithm.append($('<option value="' + key + '">' + key + '</option>'))
    }
    $algorithm.selectpicker("refresh")
}


function setClusteringParameters() {

    // If something is selected, enable the parameter modal toggle (button)
    const algo = $(this).val()
    if (algo != null && algo !== "") {
        $params.prop('disabled', false)
    } else {
        $params.prop('disabled', true)
    }

    // Disable the popover (tooltip)
    popover_params.disable()

    // Configure the modal based on selected algorithm
    $modal_body.empty()
    $modal_body.append(algo + ":")
    const $modal_container = $('<div class="container-fluid"></div>')
    const $modal_row = $('<div class="row gy-4" id="modal-row"></div>')

    const info = clustering_info[algo]
    console.log("Clustering info", info)
    const params = Object.keys(info)
    for (const p of params) {
        const id = "param_" + p
        const t = info[p]
        $modal_row.append($('<label class="col col-sm-5 col-form-label" for="' + id + '">' + p + '</label>'))

        // If it is an array --> selectpicker
        if (Array.isArray(t)) {
            const $s = makeSelectPicker(p, id, t)
            $modal_row.append($s)
            $s.selectpicker('refresh')
        } else if (t === "bool") {
            $modal_row.append($('<div class="col col-sm-7 form-check form-switch">' +
                '<input class="form-check-input" type="checkbox" role="switch" id="' + id + '" name="' + p + '">' +
                '</div>'))

        } else {
            // Default input element
            const $input = $('<input class="col col-sm-7 form-control" id="' + id + '" name="' + p + '" ' +
                'style="width: auto" type="text" data-bs-toggle="popover" data-bs-trigger="hover focus" ' +
                'data-bs-content="' + t + '">')
            $modal_row.append($input)
            const popover = new bootstrap.Popover($input.get(0))
        }


    }
    $modal_container.append($modal_row)
    $modal_body.append($modal_container)


}


function makeSelectPicker(p, id, options) {
    const $s = $('<select class="selectpicker" id="' + id + '"  title="' + p + ' ..."></select>')
    for (const opt of options) {
        $s.append($('<option value="' + opt + '">' + opt + '</option>'))
    }
    return $s
}


function getClusteringParameters() {

    // Info for selected algorithm
    const algo = $algorithm.val()
    const info = clustering_info[algo]

    const $modal_row = $('#modal-row')
    const parameters = []
    const values = []
    for (const p of $modal_row.find('input')) {
        let val = $(p).val()
        if (!val)
            continue    // skip empty inputs
        // Distinguish switches from other inputs
        if ($(p).attr('role') === "switch") {
            val = $(p).is(':checked')
            console.log(p.name, $(p).is(":checked"))
        }

        parameters.push(p.name)
        console.log(p.name, val)
        values.push(JSON.parse(val))
    }

    return [parameters, values]
}


function clearClusteringParameters() {
    const $row = $('#modal-row')
    // clear all text inputs
    $row.find('input').val('')
    // clear all selections
    for (const s of $row.find('select.selectpicker')) {
        $(s).find('option:selected').prop('selected', false)
        $(s).selectpicker('refresh')
    }
    // set all switches to unchecked
    $row.find('input[role=switch]').prop("checked", false)
}


function highlightSubgroup(evt, source_chart, needs_sort = false) {
    const elem = source_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: false}, true)
    if (elem && elem.length === 1) {
        // const dataset = elem[0].datasetIndex

        // A sort is needed if the elements index does not match the displayed subgroup's index
        // Then, index equals the top n subgroup according to selection
        let index = elem[0].index
        if (needs_sort) {
            const selection = $select_rank.val()
            const raw_data = JSON.parse(result.raw)[selection]
            const is_ascending = !($switch_rank.is(":checked"))
            const [labels, values] = sortData(raw_data, is_ascending, 5)
            index = labels[index]
        }

        // Scroll to page & row for selected subgroup
        const page_size = $table.bootstrapTable('getOptions').pageSize
        const goto_page = Math.floor(index / page_size) + 1         // page numbers start at 1 not 0...
        const scroll_index = index % page_size
        $table.bootstrapTable('selectPage', goto_page)
        $table.bootstrapTable('scrollTo', {unit: 'rows', value: scroll_index})

        // Show bars for selected subgroup
        updateSelectionChart(index)
    }
}


$(function () {

    // Add button functionality (submit task)
    $submit.click(function () {
        startFairnessTask(true)
    })
    $auto_submit.click(function () {
        startFairnessTask(false)
    })

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

    // Add click listener to highlight selected subgroup on group chart (bar) and ranking chart (bar)
    $canv_group.click(function (evt) {
        highlightSubgroup(evt, group_chart, false)      // no sort needed -> bars ordered by group index
    })

    $canv_ranking.click(function (evt) {
        highlightSubgroup(evt, ranking_chart, true)     // sort needed -> bar ordered by ranking (not group)
    })


    // Add click listener on fair chart (radar)
    $canv_fair.click(function (evt) {
        const elem = fair_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: false}, true)
        if (elem && elem.length === 1) {
            const dataset = elem[0].datasetIndex
            const index = elem[0].index
            console.log("Dataset:", dataset, "Index:", index)
            // TODO use this for something
        }
    })


    // Dataset selectpicker change listener (load dataset columns for categorical columns selection)
    $dataset.on('change', function () {
        const id = $(this).val()
        $.getJSON(columns_info_url, {id: id}, setDatasetColumns)
    })


    // Cluster algorithm select listener (if something is selected, enable parameters)
    $algorithm.on('change', setClusteringParameters);

    // Get clustering algorithm info & init algorithm selectpicker
    $.getJSON(
        clustering_info_url,
        function (data) {
            clustering_info = data
            initClusteringAlgorithms()
        }
    )

    // Cluster algorithm parameter clear all button
    $clear_params.click(clearClusteringParameters)

    // Ranking selectpicker
    $select_rank.on('change', updateRankingChart)

    // Ranking asc/desc switch
    $switch_rank.change(function () {
        let $label = $("label[for='" + $(this).attr('id') + "']");
        const label_text = ($(this).is(":checked") ? "Descending" : "Ascending")
        $label.text(label_text)
        updateRankingChart()
    })

});

