function queryParams(params) {
    console.log(params)
    // return {
    //     limit: params.pageSize,
    //     offset: params.pageSize * (params.pageNumber - 1)
    // };
    return params
}


$('#dataset-select').on('change', function () {
    const selection = $(this).val()
    let $form = $(this).closest('form');
    $form.submit()
});


