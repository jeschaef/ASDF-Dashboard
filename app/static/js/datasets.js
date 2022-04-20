let $table = $("#dstable")
let $remove = $("#remove")

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
        const url = $remove.attr("url")
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
