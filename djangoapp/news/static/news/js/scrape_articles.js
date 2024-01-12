$(document).ready(function(){
    $("#selectionForm").submit(function(event){
      event.preventDefault();
      $("#load-more-btn").addClass('d-none');
      $("#spinner").removeClass('d-none');
      $("#article-container").html('');
      $.ajax({
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function(response){
          $("#article-container").html(response.articles_html);
          $("#spinner").addClass('d-none');
          $('#load-more-btn').removeClass('d-none');
        },
        error: function(rs, e){
          alert('No more articles to scrape for selected site(s) and category!');
        }
      });
    });
    $('#load-more-btn').on('click', function() {
      $("#load-more-btn").addClass('d-none');
      $("#spinner").removeClass('d-none');
      fetch(loadMoreArticlesUrl)
        .then(response => response.json())
        .then(data => {
          $("#article-container").append(data.articles_html);
          $("#spinner").addClass('d-none');
          $('#load-more-btn').removeClass('d-none');
        })
        .catch(error => {
          alert('No more articles to scrape for selected site(s) and category!')
          console.error('Error fetching articles:', error);
        });
    });
  });