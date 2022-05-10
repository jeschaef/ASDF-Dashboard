const $status = $('#task-status')       // Task status alert
const $submit = $('#task-submit')       // Submit button (note: does not submit form)
const $switch = $('#switch')            // Positive class switch (0/1)
const $slider = $('#threshold')         // Entropy threshold (0 <= t <= 1)

// Create empty charts
const fair_chart = createFairChart()
const group_chart = createGroupChart()


function parseFairnessResult(result) {
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


function parseGroupResult(result) {

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


function updateFairChart(chart, result) {
    const [c_data, g_data] = parseFairnessResult(result)
    chart.data.datasets[0].data = c_data
    chart.data.datasets[1].data = g_data
    chart.update();
}


function updateGroupChart(chart, result) {
    // Clusters
    const k = Math.max(...result.clustering) + 1
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
        $status.fadeOut(5000)   // slowly fade out in 5s
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

            const result = JSON.parse(data['result'])
            displayResult(result)


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


function displayResult(result) {
    console.log("Finished:", result)
    
    console.log(JSON.parse(result.c_acc))

    console.log(JSON.parse(result.subgroups))

    // Plot subgroup fairness data
    updateFairChart(fair_chart, result)

    // Plot clustering/entropy-based groups data
    updateGroupChart(group_chart, result)
}


function countValues(arr) {
    const k = Math.max(...arr) + 1
    const counts = new Array(k).fill(0)     // TODO outliers
    for (const e of arr)
        counts[e] = counts[e] + 1
    return counts
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
});
