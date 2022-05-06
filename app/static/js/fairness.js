const $status = $('#task-status')       // Task status alert
const $submit = $('#task-submit')       // Submit button (note: does not submit form)


function createChart(chart_data) {

    console.log("Chart_data:", chart_data)

    const labels = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
    ];

    const data = {
        labels: labels,
        datasets: [{
            label: 'My First dataset',
            backgroundColor: 'rgb(255, 99, 132)',
            borderColor: 'rgb(255, 99, 132)',
            data: [0, 10, 5, 2, 20, 30, 45],
        }]
    };

    // Chart config
    const config = {
        type: 'line',
        data: chart_data,       // json input from html via jinja
        options: {
            layout: {
                padding: 20
            }
        }
    };

    // Create chart
    const chart = new Chart(
        document.getElementById('chart'),
        config
    );
}


function showStatus(status_msg) {
    $status.show()
    $status.text(status_msg)
}


function startFairnessTask(event) {

    // Display information
    showStatus("Starting fairness task ...")

    // Get dataset id from form
    const dataset_id = $('#dataset-select').find(":selected").val()

    // Send ajax POST request to start the task
    $.post(start_task_url,
        {dataset_id: dataset_id},
        function (data, status, request) {
            const status_url = request.getResponseHeader('Location');
            updateProgress(status_url);
        }
    ).done(function () {
        alert('Done!')
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
        showStatus("State=" + state + ": " + status)

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
}

$(function () {
    // Hide status alert at the start
    $status.hide()

    // Add button functionality
    $submit.click(startFairnessTask)

    // Create the chart
    createChart(chart_data)
});
