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

    // Add active class to anchor corresponding to current url path
    for (let i = 0; i < listItems.length; i++) {
        const anchor = listItems[i].getElementsByTagName("A")[0];
        
        if (window.location.pathname === anchor.getAttribute("href")) {
            const current = document.getElementsByClassName("active");
            current[0].className = current[0].className.replace(" active", "")
            anchor.className += " active"
        }
    }

})();
