$( function() {
    $( "#sortable" ).sortable();
    $( "#sortable" ).disableSelection();
  } );

// $('#preferenceForm').submit(function(){
// 	 $( "#sortable" ).sortable("serialize");
// }); 


$("#prefBtn").click(function(){        
	$("#order").val($( "#sortable" ).sortable( "toArray" ));
	$("#prefForm").submit();
});