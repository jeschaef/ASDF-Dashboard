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

const config = {
    type: 'line',
    data: chart_data,
    options: {
        layout: {
            padding: 20
        }
    }
};

const chart = new Chart(
    document.getElementById('chart'),
    config
);

console.log("Chart_data:", chart_data)
