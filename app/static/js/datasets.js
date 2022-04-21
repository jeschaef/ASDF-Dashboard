let $table = $("#dstable")
let $remove = $("#remove")

window.operateEvents = {
    // Click inspect operation
    'click .inspect': function (e, value, row, index) {
        console.log('Clicked row: ' + JSON.stringify(row))
        console.log('Row name: ' + row.name)

        // Add hidden form with dataset names and submit it (redirects)
        const url = $table.attr("url-inspect")
        let form = $('<form action="' + url + '" method="POST"></form>');
        let input = $("<input>")
            .attr("type", "hidden")
            .attr("name", "dataset").val(row.name);

        form.append(input)
        $('body').append(form);
        form.submit();
    }
}

function operationFormatter(value, row, index, field) {
    let element = $('<a class="inspect" href="javascript:void(0)" title="Inspect"></a>')
        .append($('<svg class="bi" width="16" height="16"><use xlink:href="#search"/></svg>'))
    return [element.prop('outerHTML')].join('')
}


function getNameSelections() {
    return $.map($table.bootstrapTable('getSelections'), function (row) {
        return row.name
    })
}

function initTable() {

    $table.bootstrapTable()
    $table.on('check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table',
        function () {
            // En-/disable delete button
            $remove.prop('disabled', !$table.bootstrapTable('getSelections').length)
        })

    // $table.on('all.bs.table', function (e, name, args) {
    //     console.log(name, args)
    // })

    $remove.click(function () {
        var names = getNameSelections()
        console.log("Selections for removal:", names)

        // Disable button
        $remove.prop('disabled', true)

        // Add hidden form with dataset names and submit it (redirects)
        const url = $table.attr("url-remove")
        let form = $('<form action="' + url + '" method="POST"></form>');
        let input = $("<input>")
            .attr("type", "hidden")
            .attr("name", "datasets").val(JSON.stringify(names));

        form.append(input)
        $('body').append(form);
        form.submit();

    })

}

$(function () {
    initTable()
})
