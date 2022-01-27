function myFunction() {
  var input, hideACs, filter, table, tr, td, i, txtValue;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");
  for (i = 1; i < tr.length; i++) { 
    ok = 0;
    ok2 = 1
    var stuff = tr[i].getElementsByTagName("td"); //.concat(tr[i].getElementsByTagName("td"));
    for (j=0;j<6;j++){
      td = stuff[j];
      if (td) {
        txtValue = td.textContent || td.innerText;
        if (txtValue.toUpperCase().includes(filter)) {
      ok = 1;
    }
    if(j == 1 && hideACs){ //somehow column 0 is yourscore
      txtValue = td.textContent || td.innerText;
      console.log(txtValue)
      if(txtValue.indexOf("100") > -1){
         ok2 = 0;
      }
    }
      }
    }
    if(!ok || !ok2){
    tr[i].style.display="none";
    }else{
    tr[i].style.display="";
    }
  }
}

function sliderchange(amt){
  var label = document.getElementById("currentDifficulty");
  label.textContent = amt.toString();
  var table = document.getElementById("myTable");
  var tr = table.getElementsByTagName("tr");
  for (i = 1; i < tr.length; i++){
    var stuff = tr[i].getElementsByTagName("td");
    if(stuff[6].innerText==amt.toString()){
      tr[i].style.display="";
    }
    else{
      tr[i].style.display="none";
    }
  }
}
