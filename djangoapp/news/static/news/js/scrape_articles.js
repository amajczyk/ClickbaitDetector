$(document).ready(function(){
    $("#selectionForm").submit(function(event){
      event.preventDefault();
      $("#spinner").removeClass('d-none');
      $.ajax({
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function(response){
          $("#article-container").append(response.articles_html);
          $("#spinner").addClass('d-none');
          $('#load-more-btn').removeClass('d-none');
        }
      });
    });
    $('#load-more-btn').on('click', function() {
      $("#load-more-btn").addClass('d-none');
      $("#spinner").removeClass('d-none');
      fetch(loadMoreArticlesUrl)
        .then(response => response.json())
        .then(data => {
          console.log(data.articles_html); // Log the data to the console
          $("#article-container").append(data.articles_html);
          $("#spinner").addClass('d-none');
          $('#load-more-btn').removeClass('d-none');
        })
        .catch(error => {
          console.error('Error fetching articles:', error);
        });
    });
  });