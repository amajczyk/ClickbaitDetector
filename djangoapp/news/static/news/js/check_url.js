$(document).ready(function(){
// Intercept form submission
$("#urlForm").submit(function(event){

    event.preventDefault(); // Prevent the form from submitting the traditional way
    
    

    $("#detailsSection").html('<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div>');

    // Perform an AJAX request
    $.ajax({
    type: $(this).attr('method'),
    url: $(this).attr('action'),
    data: $(this).serialize(),
    success: function(response){ 
        $("#detailsSection").html(response.html);
        }
    });


});
});
