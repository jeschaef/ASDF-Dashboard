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

        // Instead remove, perform
        $table.bootstrapTable('remove', {
            field: 'name',
            values: names
        })
        $remove.prop('disabled', true)
    })

}

$(function () {
    initTable()
})
