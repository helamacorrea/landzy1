//select elements
const year = document.querySelector("#current-year");
const lastModified = document.querySelector("#last-modified");

//create date object
const today = new Date();

//set current year
year.innerHTML = today.getFullYear();

// set last modified date
lastModified.innerHTML = `Last Modified: ${document.lastModified}`;