/* global bootstrap: false */
(function () {
    'use strict'
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl)
    })
})();


(function () {
    // Get all list items in nav list
    const navList = document.getElementById("navList");
    const listItems = navList.getElementsByClassName("nav-item");
    console.log(listItems)

    // Add event listeners that on click set the active class to the clicked anchor
    for (let i = 0; i < listItems.length; i++) {
        const anchor = listItems[i].getElementsByTagName("A")[0];
        anchor.addEventListener("click", function () {
            const current = document.getElementsByClassName("active");
            current[0].className = current[0].className.replace(" active", "")
            this.className += " active"
        })
    }
})();
