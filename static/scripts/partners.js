const cities = [
  {
    id: "cx-1888",
    name: "Caxias do Sul",
    state: "RS"
  },
  {
    id: "fcr-2050",
    name: "Farroupilha",
    state: "RS"
  },
  {
    id: "It-1987",
    name: "Itapema",
    state: "SC"
  },
  {
    id: "ac-2000",
    name: "Acre",
    state: "AA"
  },
  {
    id: "ot-0000",
    name: "- Other",
    state: ""
  }
];


const options = document.querySelector('#productId');
const submit = document.querySelector('input[type="submit"]');
let htmlOp = '<option value="" disabled selected>Select a Product</option>';


cities.forEach(city => {
    htmlOp += `<option value=${city.id}>${city.name} - ${city.state}</option>\n`
});

options.innerHTML = htmlOp;




