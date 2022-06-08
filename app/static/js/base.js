(function () {
    let $info_modal = $('#info-modal')

    // Update and show modal with status information
    if (show_info_modal) {
        let modal = new bootstrap.Modal($info_modal.get(0), {})
        modal.show()
    }

})()