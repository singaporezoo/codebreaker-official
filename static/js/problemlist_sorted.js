// IDK if this works but hopefully this will get executed on start
// Query the table
const table = document.getElementById("myTable");

// Query the headers
const headers = table.querySelectorAll('th');
let cur = -1;

// Loop over the headers
[].forEach.call(headers, function(header, index) {
    header.addEventListener("click", function() {
        // This function will sort the column
        sortColumn(index);
    });
});

// Helper function for sorting rows
// Transform the content of given cell in given column
const transform = function(index, content) {
    // Get the data type of column
    const type = headers[index].getAttribute('data-type');
    switch (type) {
	case 'score':
	    // To account for the N/A possbility as a result in score
	    if (content.trim() == "N/A") return 1;
	    else return - parseInt(content.trim())
        case 'int':
	    // For integer parameters, it is to be reversed
            return - parseInt(content.trim());
        case 'string':
	    // Ignore case when sorting and whitespace
	    return content.toLowerCase().trim();
        default:
            return content;
    }
};

const sortColumn = function(index) {
    const invert = (index === cur);
    cur = (invert ? -1 : index);
    // Get the table
    const tableBody = table.querySelector('tbody');
    const rows = tableBody.querySelectorAll('tr');
    
    // Clone the rows
    const newRows = Array.from(rows);

    // Sort rows by the content of cells
    newRows.sort(function(rowA, rowB) {
        if (invert) [rowA, rowB]=[rowB, rowA];
	// Get the content of cells
	const cellA = rowA.querySelectorAll('td')[index];
        const cellB = rowB.querySelectorAll('td')[index];

	const a = transform(index, cellA.textContent || cellA.innerText);
	const b = transform(index, cellB.textContent || cellB.innerText);

        /*switch (true) {
            case a > b: return 1;
            case a < b: return -1;
            case a == b: return 0;
        }*/
	
	return a.localeCompare(b,"en",{numeric:true});
    });

    // Remove old rows
    [].forEach.call(rows, function(row) {
        tableBody.removeChild(row);
    });

    // Append new row
    newRows.forEach(function(newRow) {
        tableBody.appendChild(newRow);
    });
}
